# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel Sverige AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import json
import logging

from html import escape

from odoo import http
from odoo.http import request, Response
from odoo.tools import ustr

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Ärvd backend-manifest-override. Vi ärver OCA:s WebManifest-klass (som i sin
# tur ärver Odoos) och dekorrerar om samma route — OCA gör exakt detta mot
# Odoos web-manifest, och vår modul laddas efter web_pwa_customize (depends).
# ---------------------------------------------------------------------------
try:
    from odoo.addons.web_pwa_customize.controllers.webmanifest import (
        WebManifest as OcaWebManifest,
    )
except Exception:  # pragma: no cover
    OcaWebManifest = None

_PWA_ICON_URL_BASE = '/web_pwa_push/icon'

# ---------------------------------------------------------------------------
# Service worker — pass-through + push-listener.
# Ingen cache: respekterar sidors Cache-Control: no-store (t.ex. /ai/chat).
# Scope för /ai/ kontrolleras via headern Service-Worker-Allowed (sätts i
# route-metoden).
# ---------------------------------------------------------------------------
_SW_JS = r"""// PWA Push — pass-through service worker
// Ingen cache: respekterar no-store-sidor (t.ex. /ai/chat).
self.addEventListener('install', (event) => {
    self.skipWaiting();
});
self.addEventListener('activate', (event) => {
    event.waitUntil(self.clients.claim());
});
self.addEventListener('fetch', (event) => {
    event.respondWith(fetch(event.request));
});
self.addEventListener('push', (event) => {
    if (!event.data) return;
    let notification;
    try {
        notification = event.data.json();
    } catch (e) {
        notification = { title: 'Odoo', body: event.data.text() };
    }
    const options = Object.assign({}, notification.options || {});
    options.data = options.data || {};
    options.icon = options.icon || '/web_pwa_push/icon192x192.png';
    options.badge = options.badge || '/web_pwa_push/icon192x192.png';
    event.waitUntil(self.registration.showNotification(notification.title || 'Odoo', options));
});
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    const url = (event.notification.data && event.notification.data.url) || '/';
    event.waitUntil(clients.matchAll({ type: 'window', includeUncontrolled: true }).then((list) => {
        for (const client of list) {
            if ('focus' in client) {
                client.focus();
                if ('navigate' in client) client.navigate(url);
                return;
            }
        }
        return clients.openWindow(url);
    }));
});
self.addEventListener('pushsubscriptionchange', async (event) => {
    if (!event.oldSubscription) return;
    const subscription = await self.registration.pushManager.subscribe(event.oldSubscription.options);
    await fetch('/web/dataset/call_kw/mail.push.device/register_devices', {
        headers: { 'Content-type': 'application/json' },
        body: JSON.stringify({
            id: 1, jsonrpc: '2.0', method: 'call',
            params: {
                model: 'mail.push.device', method: 'register_devices', args: [],
                kwargs: { ...subscription.toJSON(), previousEndpoint: event.oldSubscription.endpoint },
                context: {},
            },
        }),
        method: 'POST', mode: 'cors', credentials: 'include',
    });
});
"""


class PwaController(http.Controller):

    # ------------------------------------------------------------------
    # Service worker (kontrollerar /ai/ via Service-Worker-Allowed)
    # ------------------------------------------------------------------
    @http.route('/pwa/sw.js', type='http', auth='public', methods=['GET'], sitemap=False)
    def pwa_sw(self):
        return Response(
            _SW_JS,
            headers=[
                ('Content-Type', 'text/javascript'),
                ('Cache-Control', 'no-store, must-revalidate'),
                ('Service-Worker-Allowed', self._sw_scope()),
            ])

    # ------------------------------------------------------------------
    # Manifest per registrerad app (start_url/scope definierar appen,
    # inte URL:en den serveras från).
    # ------------------------------------------------------------------
    @http.route('/pwa/manifest/<string:key>', type='http', auth='public',
                methods=['GET'], sitemap=False)
    def pwa_manifest(self, key, **kw):
        """Serve the manifest of a registered app.

        Apps live in web.pwa.app, so a module adds its app as data instead of
        this controller growing a branch per app. The key 'ai-chat' is kept as
        an alias for the chat app: it is the URL already installed on devices
        and must keep working.
        """
        app = request.env['web.pwa.app'].sudo()._get_app(key)
        if not app:
            return request.not_found()
        return request.make_json_response(app.get_manifest(), {
            'Content-Type': 'application/manifest+json'})

    # ------------------------------------------------------------------
    # Bakåtkompatibilitet: /pwa/manifest/ai-chat är redan installerad på
    # enheter i drift. Den behåller exakt samma svar som tidigare.
    # ------------------------------------------------------------------
    @http.route('/pwa/manifest/ai-chat', type='http', auth='public',
                methods=['GET'], sitemap=False)
    def pwa_manifest_ai_chat(self):
        company = request.env.company.sudo()
        manifest = {
            'name': company.pwa_app_name('chat'),
            'short_name': company.pwa_app_name('chat')[:12],
            'start_url': '/ai/chat',
            'scope': '/ai/',
            'display': 'standalone',
            'background_color': self._pwa_color('background'),
            'theme_color': self._pwa_color('theme'),
            'icons': [
                {'src': '/web_pwa_push/icon192x192.png', 'sizes': '192x192', 'type': 'image/png'},
                {'src': '/web_pwa_push/icon512x512.png', 'sizes': '512x512', 'type': 'image/png',
                 'purpose': 'any maskable'},
            ],
        }
        return request.make_json_response(manifest, {
            'Content-Type': 'application/manifest+json'})

    # ------------------------------------------------------------------
    # Kamera-ingång (Alt 2a: tunn). web_pwa_push vet inte vad en bild är —
    # den renderar en filväljare och postar till appens callback.
    # ------------------------------------------------------------------
    @http.route('/pwa/capture', type='http', auth='user', methods=['GET'],
                sitemap=False)
    def pwa_capture(self, app=None, **kw):
        pwa_app = request.env['web.pwa.app'].sudo().search(
            [('key', '=', app or ''), ('capture_enabled', '=', True)], limit=1)
        if not pwa_app:
            return request.not_found()
        html = _CAPTURE_HTML.replace('__APP_KEY__', escape(pwa_app.key))
        html = html.replace('__ACCEPT__', escape(pwa_app.capture_accept or 'image/*'))
        html = html.replace('__TITLE__', escape(
            pwa_app.name or request.env.company.sudo().pwa_app_name(pwa_app.key)))
        return Response(html, headers=[
            ('Content-Type', 'text/html; charset=utf-8'),
            ('Cache-Control', 'no-store, must-revalidate')])

    @http.route('/pwa/upload', type='http', auth='user', methods=['POST'],
                csrf=False, sitemap=False)
    def pwa_upload(self, app=None, **kw):
        """Hand the uploaded files to the app's callback.

        The callback runs with the user's own env - no sudo. Access is decided
        by the app that owns the data, never here.
        """
        pwa_app = request.env['web.pwa.app'].sudo().search(
            [('key', '=', app or ''), ('capture_enabled', '=', True)], limit=1)
        if not pwa_app:
            return request.not_found()
        if not pwa_app.capture_model or not pwa_app.capture_method:
            return request.make_json_response(
                {'error': 'app has no capture callback'}, status=500)
        model = request.env.get(pwa_app.capture_model)
        if model is None:
            return request.make_json_response(
                {'error': 'unknown model %s' % pwa_app.capture_model}, status=500)
        callback = getattr(model, pwa_app.capture_method, None)
        if callback is None:
            return request.make_json_response(
                {'error': 'unknown method %s' % pwa_app.capture_method},
                status=500)
        files = request.httprequest.files.getlist('file')
        if not files:
            return request.make_json_response(
                {'error': 'no file uploaded'}, status=400)
        try:
            result = callback(files, **kw)
        except Exception as error:  # noqa: BLE001 - reported to the client
            _logger.exception("pwa capture callback failed")
            return request.make_json_response(
                {'error': str(error)}, status=400)
        return request.make_json_response(result)

    # ------------------------------------------------------------------
    # Publik VAPID-nyckel — för push-registrering från fristående sidor
    # (t.ex. /ai/chat). Nyckeln är publik av design.
    # ------------------------------------------------------------------
    @http.route('/pwa/vapid-public-key', type='http', auth='public', methods=['GET'], sitemap=False)
    def pwa_vapid_public_key(self):
        key = request.env['mail.push.device'].sudo().get_web_push_vapid_public_key()
        return request.make_json_response({'vapid_public_key': key})

    # ------------------------------------------------------------------
    # Install-hubb (generisk, valfri) — lista registrerade appar
    # ------------------------------------------------------------------
    @http.route('/pwa/install', type='http', auth='public', methods=['GET'], sitemap=False)
    def pwa_install(self, **kw):
        company = request.env.company.sudo()
        apps = self._pwa_install_apps(company)
        cards = '\n'.join(self._pwa_install_card(app) for app in apps)
        html = _INSTALL_HTML.replace('<!-- APP_CARDS -->', cards)
        return Response(html, headers=[
            ('Content-Type', 'text/html; charset=utf-8'),
            ('Cache-Control', 'no-store, must-revalidate')])

    def _sw_scope(self):
        """Service-Worker-Allowed value.

        '/' by default: one worker per origin, so a page under /ai/ can
        register a worker that also controls the capture route. Narrowing it
        back to '/ai/' would silently break every scope outside /ai/.
        """
        return '/'

    def _pwa_install_apps(self, company):
        """Apps shown in the install hub, from the web.pwa.app registry.

        The registry is the source of truth. 'ai-chat' and 'odoo' are seeded
        as data by this module, so the hub looks the same as before; any
        module that adds an app gets a card for free.
        """
        apps = request.env['web.pwa.app'].sudo().search(
            [('active', '=', True)])
        cards = []
        for app in apps:
            cards.append({
                'key': app.key,
                'title': app.name or company.pwa_app_name(app.key),
                'desc': app.description or '',
                'manifest': '/pwa/manifest/%s' % app.key,
                'href': app.install_href or app.start_url or '/',
                'icon': app.icon_url or '/web_pwa_push/icon192x192.png',
            })
        return cards

    def _pwa_install_card(self, app):
        return """
        <div class="app-card" data-manifest="%s" data-href="%s">
            <img class="app-icon" src="%s" alt="%s"/>
            <div class="app-info">
                <div class="app-title">%s</div>
                <div class="app-desc">%s</div>
            </div>
            <button class="install-btn" type="button">Installera</button>
            <a class="open-link" href="%s">Öppna</a>
        </div>
        """ % (escape(app['manifest']), escape(app['href']), escape(app['icon']),
               escape(app['title']), escape(app['title']), escape(app['desc']),
               escape(app['href']))

    def _pwa_color(self, kind):
        key = 'pwa.manifest.%s_color' % kind
        return request.env['ir.config_parameter'].sudo().get_param(key, '#1a1a2e')


if OcaWebManifest is not None:
    class WebManifest(OcaWebManifest):
        """Kundbrandat backend-manifest (/web/manifest.webmanifest).

        Ärver OCA:s klass (route ärvs — samma mönster som OCA mot Odoo) men
        anropar Odoos ORIGINAL webmanifest (OCA:s letar hårdkodat efter
        /web_pwa_customize/icon) och applicerar branding med vår ikon-base.
        """

        @http.route('/web/manifest.webmanifest', type='http', auth='public',
                    methods=['GET'], readonly=True)
        def webmanifest(self):
            from odoo.addons.web.controllers.webmanifest import WebManifest as OdooWebManifest
            # super(OcaWebManifest, self) → Odoos original (OcaWebManifest ärver Odoos)
            res = super(OcaWebManifest, self).webmanifest()
            manifest = json.loads(res.response[0])
            icp = request.env['ir.config_parameter'].sudo()
            manifest['name'] = request.env.company.sudo().pwa_app_name('backend')
            manifest['short_name'] = icp.get_param(
                'pwa.manifest.short_name', manifest.get('name', 'Odoo'))
            manifest['background_color'] = icp.get_param(
                'pwa.manifest.background_color', '#714B67')
            manifest['theme_color'] = icp.get_param(
                'pwa.manifest.theme_color', '#714B67')
            pwa_icon = request.env['ir.attachment'].sudo().search(
                [('url', 'like', _PWA_ICON_URL_BASE + '.')], limit=1)
            if pwa_icon:
                manifest['icons'] = self._get_pwa_manifest_icons(pwa_icon)
            body = json.dumps(manifest, default=ustr)
            return request.make_response(body, [
                ('Content-Type', 'application/manifest+json')])

        def _get_pwa_manifest_icons(self, pwa_icon):
            """Samma mönster som OCA men med vår ikon-base (/web_pwa_push/icon)."""
            icons = []
            if not pwa_icon.mimetype.startswith('image/svg'):
                all_icons = request.env['ir.attachment'].sudo().search([
                    ('url', 'like', _PWA_ICON_URL_BASE),
                    ('url', 'not like', _PWA_ICON_URL_BASE + '.'),
                ])
                for icon in all_icons:
                    icon_size_name = icon.url.split('/')[-1].lstrip('icon').split('.')[0]
                    icons.append({
                        'src': icon.url,
                        'sizes': icon_size_name,
                        'type': icon.mimetype,
                    })
            else:
                icons = [{
                    'src': pwa_icon.url,
                    'sizes': '128x128 144x144 152x152 192x192 256x256 512x512',
                    'type': pwa_icon.mimetype,
                }]
            return icons


# ---------------------------------------------------------------------------
# Install-hubb HTML (lätt, generisk). Manuella vägen är ALLTID synlig —
# prompten är en lyx, inte en förutsättning (lärdom från ai-chat-pwa-testet).
# ---------------------------------------------------------------------------
_INSTALL_HTML = r"""<!DOCTYPE html>
<html lang="sv">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no"/>
<title>Installera appar</title>
<style>
:root { --bg:#fff; --card:#f5f7fa; --border:#e0e0e0; --text:#1a1a2e; --muted:#666;
        --accent:#1976d2; --radius:12px;
        --font:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; }
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:var(--font); background:var(--bg); color:var(--text);
       min-height:100vh; display:flex; align-items:center; justify-content:center; padding:24px; }
.container { width:100%; max-width:440px; }
h1 { font-size:22px; margin-bottom:4px; }
.sub { color:var(--muted); font-size:14px; margin-bottom:20px; }
.app-card { background:var(--card); border:1px solid var(--border); border-radius:var(--radius);
            padding:16px; display:flex; align-items:center; gap:14px; margin-bottom:12px; }
.app-icon { width:56px; height:56px; border-radius:12px; object-fit:cover; background:#fff; }
.app-info { flex:1; }
.app-title { font-weight:600; font-size:16px; }
.app-desc { color:var(--muted); font-size:13px; }
.install-btn { background:var(--accent); color:#fff; border:none; border-radius:8px;
               padding:8px 14px; font-size:14px; font-weight:600; cursor:pointer; }
.open-link { color:var(--accent); font-size:14px; text-decoration:none; }
.note { margin-top:16px; color:var(--muted); font-size:13px; line-height:1.5; }
.ios-step { display:flex; align-items:center; gap:8px; margin-top:8px; }
.kbd { background:#fff; border:1px solid var(--border); border-radius:6px; padding:2px 8px;
       font-size:12px; font-weight:600; }
</style>
</head>
<body>
<div class="container">
<h1>Installera appar</h1>
<div class="sub">Lägg apparna på hemskärmen — precis som en vanlig app.</div>
<!-- APP_CARDS -->
<div class="note">
<div><b>Android:</b> tryck <b>Installera</b> — eller webbläsarmenyn <span class="kbd">⋮</span> → <b>Installera app</b>.</div>
<div class="ios-step"><b>iPhone:</b> <span class="kbd">Dela</span> → <b>Lägg till på hemskärmen</b>.</div>
</div>
</div>
<script>
(function () {
    var isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent);
    var deferredPrompt = null;

    window.addEventListener('beforeinstallprompt', function (e) {
        e.preventDefault();
        deferredPrompt = e;
        var btns = document.querySelectorAll('.install-btn');
        for (var i = 0; i < btns.length; i++) btns[i].style.display = 'inline-block';
    });

    var installBtns = document.querySelectorAll('.install-btn');
    for (var j = 0; j < installBtns.length; j++) {
        installBtns[j].addEventListener('click', function () {
            if (!deferredPrompt) return;
            deferredPrompt.prompt();
            deferredPrompt.userChoice.then(function () { deferredPrompt = null; });
        });
    }

    if (isIOS) {
        for (var k = 0; k < installBtns.length; k++) installBtns[k].style.display = 'none';
    }

    // Installerad-status (Android/Chrome; progressiv förbättring)
    if (navigator.getInstalledRelatedApps) {
        navigator.getInstalledRelatedApps().then(function (apps) {
            var cards = document.querySelectorAll('.app-card');
            for (var c = 0; c < cards.length; c++) {
                var href = cards[c].getAttribute('data-href');
                for (var a = 0; a < apps.length; a++) {
                    if (apps[a].id === location.origin + href) {
                        cards[c].querySelector('.app-title').textContent += ' ✓';
                    }
                }
            }
        }).catch(function () {});
    }
})();
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Capture-sida (Alt 2a: tunn). En filväljare, en förhandsvisning, en
# uppladdningsknapp. Ingen beskärning, ingen komprimering — det hör i appen
# som äger datat, inte här.
# ---------------------------------------------------------------------------
_CAPTURE_HTML = r"""<!DOCTYPE html>
<html lang="sv">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no"/>
<title>__TITLE__</title>
<style>
:root { --bg:#fff; --card:#f5f7fa; --border:#e0e0e0; --text:#1a1a2e; --muted:#666;
        --accent:#1976d2; --radius:12px;
        --font:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; }
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:var(--font); background:var(--bg); color:var(--text);
       min-height:100vh; padding:24px; }
.container { max-width:520px; margin:0 auto; }
h1 { font-size:20px; margin-bottom:16px; }
.pick { display:block; background:var(--card); border:2px dashed var(--border);
        border-radius:var(--radius); padding:32px 16px; text-align:center;
        cursor:pointer; margin-bottom:16px; }
.pick:active { background:#eef2f7; }
.pick-icon { font-size:40px; line-height:1; }
.pick-text { margin-top:8px; font-weight:600; }
.pick-sub { color:var(--muted); font-size:13px; margin-top:4px; }
input[type=file] { display:none; }
.preview { display:none; margin-bottom:16px; }
.preview img { width:100%; border-radius:var(--radius); border:1px solid var(--border); }
.preview .name { color:var(--muted); font-size:13px; margin-top:6px; word-break:break-all; }
button.send { width:100%; background:var(--accent); color:#fff; border:none;
              border-radius:var(--radius); padding:14px; font-size:16px;
              font-weight:600; cursor:pointer; }
button.send:disabled { background:#b0bec5; }
.status { margin-top:16px; font-size:14px; line-height:1.5; }
.status.ok { color:#2e7d32; }
.status.err { color:#c62828; }
</style>
</head>
<body>
<div class="container">
<h1>__TITLE__</h1>
<label class="pick" for="file">
    <div class="pick-icon">📷</div>
    <div class="pick-text">Ta bild eller välj fil</div>
    <div class="pick-sub">JPG, PNG eller PDF</div>
</label>
<input id="file" type="file" accept="__ACCEPT__" capture="environment"/>
<div class="preview" id="preview">
    <img id="preview-img" alt=""/>
    <div class="name" id="preview-name"></div>
</div>
<button class="send" id="send" type="button" disabled>Ladda upp</button>
<div class="status" id="status"></div>
</div>
<script>
(function () {
    var appKey = "__APP_KEY__";
    var input = document.getElementById('file');
    var preview = document.getElementById('preview');
    var previewImg = document.getElementById('preview-img');
    var previewName = document.getElementById('preview-name');
    var send = document.getElementById('send');
    var status = document.getElementById('status');
    var chosen = null;

    input.addEventListener('change', function () {
        chosen = input.files && input.files[0];
        if (!chosen) return;
        previewName.textContent = chosen.name + ' (' + Math.round(chosen.size / 1024) + ' kB)';
        if (chosen.type.indexOf('image/') === 0) {
            previewImg.src = URL.createObjectURL(chosen);
            previewImg.style.display = 'block';
        } else {
            previewImg.style.display = 'none';
        }
        preview.style.display = 'block';
        send.disabled = false;
        status.textContent = '';
        status.className = 'status';
    });

    send.addEventListener('click', function () {
        if (!chosen) return;
        send.disabled = true;
        status.textContent = 'Laddar upp…';
        status.className = 'status';
        var form = new FormData();
        form.append('file', chosen);
        fetch('/pwa/upload?app=' + encodeURIComponent(appKey), {
            method: 'POST',
            body: form,
            credentials: 'include',
        }).then(function (response) {
            return response.json().then(function (body) {
                return { ok: response.ok, body: body };
            });
        }).then(function (result) {
            if (result.ok) {
                status.textContent = 'Uppladdad.';
                status.className = 'status ok';
                chosen = null;
                input.value = '';
                preview.style.display = 'none';
            } else {
                status.textContent = 'Fel: ' + (result.body.error || 'okänt fel');
                status.className = 'status err';
                send.disabled = false;
            }
        }).catch(function (error) {
            status.textContent = 'Nätverksfel: ' + error.message;
            status.className = 'status err';
            send.disabled = false;
        });
    });
})();
</script>
</body>
</html>
"""
