# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel Sverige AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import json
import logging
import time

from odoo import http
from odoo.exceptions import AccessDenied
from odoo.http import Response, request

import werkzeug.wrappers

_logger = logging.getLogger(__name__)

# Longpoll: how often to look for new rows, and when to give up. ntfy clients
# expect the stream to stay open; 30s keeps the request inside a normal proxy
# timeout (Caddy defaults well above this) while releasing the worker between
# polls.
POLL_INTERVAL = 2.0
POLL_TIMEOUT = 30.0

# ntfy's own limits; a client that asks for more gets truncated.
MAX_TITLE = 256
MAX_BODY = 4096


class NtfyController(http.Controller):
    """The ntfy protocol, under /ntfy/.

    Deliberately no web UI: Odoo is the UI. That is also why the upstream
    "subdomain required" constraint does not apply here — it exists because
    the ntfy web app emits absolute /static/ paths, which we never serve.
    """

    # ── helpers ──────────────────────────────────────────────────────────

    def _json_response(self, payload, status=200):
        return Response(
            json.dumps(payload),
            status=status,
            mimetype='application/json',
        )

    def _error(self, status, message):
        return self._json_response({'error': message, 'code': status}, status=status)

    def _auth_user(self):
        """Resolve the caller to a user, or None.

        Two ways in:
          * a normal Odoo session (the browser, and anything holding a cookie)
          * Authorization: Bearer <token> (cron jobs; see ntfy.token)

        Note: routes are declared `auth='none'`, which means Odoo does NOT load
        the session user into `request.env` — `request.env.user` is always the
        public user there. The session id is still parsed, so the uid has to be
        read from `request.session` and the user looked up explicitly.
        """
        auth = request.httprequest.headers.get('Authorization', '')
        if auth.startswith('Bearer '):
            raw = auth[len('Bearer '):].strip()
            try:
                return request.env['ntfy.token'].sudo()._authenticate(raw)
            except AccessDenied:
                return None
        uid = request.session.uid
        if not uid:
            return None
        user = request.env['res.users'].sudo().browse(uid)
        if not user.exists() or not user.active or user._is_public():
            return None
        return user

    def _topic_owner(self, topic):
        """Return the user owning `topic`, or an empty recordset."""
        return request.env['ntfy.topic'].sudo()._user_for_topic(topic)

    def _authorized(self, topic):
        """Return the user if they may read/write `topic`.

        Three outcomes, and they must stay distinct so the caller can answer
        with the right status:
          * None  — not authenticated (401)
          * False — authenticated, but the topic is not theirs (403)
          * user  — allowed
        An unknown topic is a 404, handled by the caller before this runs.
        """
        user = self._auth_user()
        if not user:
            return None
        owner = self._topic_owner(topic)
        if not owner:
            return 'unknown'
        return user if owner.id == user.id else False

    def _enabled(self):
        return request.env['ntfy.topic'].sudo()._is_enabled()

    # ── publishing ───────────────────────────────────────────────────────

    @http.route([
        '/ntfy/<string:topic>',
        '/ntfy/<string:topic>/',
    ], type='http', auth='none', methods=['POST', 'PUT'], csrf=False, save_session=False)
    def publish(self, topic, **kw):
        """POST/PUT /ntfy/{topic} — the ntfy publish API."""
        if not self._enabled():
            return self._error(404, 'ntfy is not enabled')
        allowed = self._authorized(topic)
        if allowed is None:
            return self._error(401, 'authentication required')
        if allowed == 'unknown':
            return self._error(404, 'unknown topic')
        if allowed is False:
            return self._error(403, 'topic does not belong to you')

        headers = request.httprequest.headers
        # Body: ntfy accepts a plain-text body or a JSON publish message.
        raw = request.httprequest.get_data(as_text=True) or ''
        title = headers.get('X-Title') or headers.get('Title')
        body = raw
        priority = headers.get('X-Priority') or headers.get('Priority')
        tags = headers.get('X-Tags') or headers.get('Tags')
        click = headers.get('X-Click') or headers.get('Click')
        actions = headers.get('X-Actions') or headers.get('Actions')

        if raw.strip().startswith('{'):
            try:
                data = json.loads(raw)
            except ValueError:
                return self._error(400, 'invalid JSON body')
            title = data.get('title', title)
            body = data.get('message', '') or ''
            priority = data.get('priority', priority)
            click = data.get('click', click)
            raw_tags = data.get('tags')
            if raw_tags and not tags:
                tags = ','.join(raw_tags) if isinstance(raw_tags, list) else str(raw_tags)
            raw_actions = data.get('actions')
            if raw_actions and not actions:
                actions = '\n'.join(
                    ','.join('%s=%s' % (k, v) for k, v in a.items())
                    if isinstance(a, dict) else str(a)
                    for a in raw_actions
                )

        # ntfy maps numeric priorities onto names.
        numeric = {'1': 'min', '2': 'low', '3': 'default', '4': 'high', '5': 'max'}
        if priority in numeric:
            priority = numeric[priority]

        message = request.env['ntfy.message'].sudo()._publish(
            allowed,
            title=(title or '')[:MAX_TITLE] or None,
            body=(body or '')[:MAX_BODY] or None,
            priority=priority if priority in ('min', 'low', 'default', 'high', 'max') else None,
            tags=tags,
            click=click,
            actions=actions,
        )
        return self._json_response(message._to_ntfy_json())

    # ── subscribing ──────────────────────────────────────────────────────

    @http.route(
        '/ntfy/<string:topic>/json',
        type='http', auth='none', methods=['GET'], csrf=False, save_session=False,
    )
    def subscribe_json(self, topic, **kw):
        """GET /ntfy/{topic}/json — the JSON stream, or a poll when asked."""
        if not self._enabled():
            return self._error(404, 'ntfy is not enabled')
        allowed = self._authorized(topic)
        if allowed is None:
            return self._error(401, 'authentication required')
        if allowed == 'unknown':
            return self._error(404, 'unknown topic')
        if allowed is False:
            return self._error(403, 'topic does not belong to you')

        since = kw.get('since')
        is_poll = kw.get('poll') in ('1', 'true', 'True')

        if is_poll:
            messages = request.env['ntfy.message'].sudo()._since(topic, since or 'all')
            payload = '\n'.join(json.dumps(m._to_ntfy_json()) for m in messages)
            return Response(payload, mimetype='application/x-ndjson')

        return self._stream(topic, since, sse=False)

    @http.route(
        '/ntfy/<string:topic>/sse',
        type='http', auth='none', methods=['GET'], csrf=False, save_session=False,
    )
    def subscribe_sse(self, topic, **kw):
        """GET /ntfy/{topic}/sse — the same stream as Server-Sent Events."""
        if not self._enabled():
            return self._error(404, 'ntfy is not enabled')
        allowed = self._authorized(topic)
        if allowed is None:
            return self._error(401, 'authentication required')
        if allowed == 'unknown':
            return self._error(404, 'unknown topic')
        if allowed is False:
            return self._error(403, 'topic does not belong to you')
        return self._stream(topic, kw.get('since'), sse=True)

    def _stream(self, topic, since, sse=False):
        """Longpoll the message table and emit new rows as they appear.

        Returns a werkzeug Response wrapping a generator: Odoo's own
        `_Response.load` rejects bare generators, but accepts a werkzeug
        response whose body is one (is_streamed=True).

        Opening a cursor per poll and committing between iterations is what
        lets this see rows written by other requests — a single long-lived
        transaction would be stuck in its own snapshot.
        """
        message_model = request.env['ntfy.message'].sudo()
        seen = set()
        if since and since != 'all':
            seen = {m.id for m in message_model._since(topic, since)}

        def generate():
            deadline = time.time() + POLL_TIMEOUT
            while time.time() < deadline:
                request.env.cr.commit()  # end the snapshot so new rows are visible
                domain = [('topic', '=', topic)]
                if seen:
                    domain.append(('id', 'not in', list(seen)))
                candidates = message_model.search(domain, order='id asc', limit=100)
                for message in candidates:
                    seen.add(message.id)
                    data = json.dumps(message._to_ntfy_json())
                    if sse:
                        yield 'data: %s\n\n' % data
                    else:
                        yield data + '\n'
                time.sleep(POLL_INTERVAL)

            # Final keepalive so the client knows the server is alive on an
            # idle topic; ntfy clients treat this as a no-op event.
            keepalive = {'event': 'keepalive', 'topic': topic, 'time': int(time.time())}
            if sse:
                yield 'data: %s\n\n' % json.dumps(keepalive)
            else:
                yield json.dumps(keepalive) + '\n'

        mimetype = 'text/event-stream' if sse else 'application/x-ndjson'
        response = werkzeug.wrappers.Response(generate(), mimetype=mimetype)
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['X-Accel-Buffering'] = 'no'
        return response

    # ── token exchange ───────────────────────────────────────────────────

    @http.route(
        '/ntfy/auth',
        type='http', auth='none', methods=['POST'], csrf=False, save_session=False,
    )
    def auth(self, **kw):
        """Exchange an Odoo API key for a short-lived Bearer token.

        A browser holds a session cookie; a cron job does not. Those call here
        with their Odoo API key and get a token valid for 24 hours.
        """
        if not self._enabled():
            return self._error(404, 'ntfy is not enabled')
        data = {}
        raw = request.httprequest.get_data(as_text=True) or ''
        if raw.strip().startswith('{'):
            try:
                data = json.loads(raw)
            except ValueError:
                return self._error(400, 'invalid JSON body')
        login = data.get('login') or kw.get('login')
        api_key = data.get('api_key') or kw.get('api_key')
        if not login or not api_key:
            return self._error(400, 'login and api_key are required')

        # Validate against Odoo's own credential check so we never invent a
        # second authentication path. Odoo 18 takes a credential dict, not
        # separate login/password arguments.
        try:
            auth_info = request.env['res.users'].sudo().authenticate(
                request.env.cr.dbname,
                {'type': 'password', 'login': login, 'password': api_key},
                {'interactive': False},
            )
        except AccessDenied:
            return self._error(401, 'invalid credentials')
        except Exception:  # noqa: BLE001
            _logger.exception('web_ntfy: auth lookup failed for %s', login)
            return self._error(401, 'invalid credentials')
        uid = (auth_info or {}).get('uid')
        if not uid:
            return self._error(401, 'invalid credentials')

        user = request.env['res.users'].sudo().browse(uid)
        token = request.env['ntfy.token'].sudo()._issue(user)
        return self._json_response({
            'token': token,
            'topic': request.env['ntfy.topic'].sudo()._topic_for_user(user),
            'expires_in': 24 * 3600,
        })
