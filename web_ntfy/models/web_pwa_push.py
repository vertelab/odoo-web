# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel Sverige AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import json
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class WebPwaPush(models.AbstractModel):
    """Fan-out: one call, every enabled transport.

    Before this module `_push_user_notification` did exactly one thing — queue
    a web push. It now dispatches, but the signature and the return value are
    backward compatible: existing callers (ai_agent_core's done-notification
    and HITL prompts) pass the same arguments and get the same answer.

    The point of fanning out here rather than adding an ntfy hook elsewhere is
    that callers must not have to know ntfy exists. Same shape as
    saltstack.alert in the base module with thin additions on top.
    """

    _inherit = 'web.pwa.push'

    @api.model
    def _enabled_transports(self):
        """Return the transports enabled in settings, as a set of names."""
        icp = self.env['ir.config_parameter'].sudo()
        transports = set()
        if icp.get_param('web_ntfy.transport_web_push', 'True') == 'True':
            transports.add('web_push')
        if icp.get_param('web_ntfy.enabled', 'False') == 'True' and \
                icp.get_param('web_ntfy.transport_ntfy', 'True') == 'True':
            transports.add('ntfy')
        return transports

    @api.model
    def _push_user_notification(self, user, title, body, url=None, icon=None,
                                transports=None):
        """Deliver a notification to a user over every enabled transport.

        :param transports: optional explicit set of transport names; when
            omitted the server settings decide. Existing callers pass nothing.
        :return: True if at least one transport accepted the notification.
        """
        if transports is None:
            transports = self._enabled_transports()
        delivered = False
        if 'web_push' in transports:
            delivered = self._push_web_push(user, title, body, url, icon) or delivered
        if 'ntfy' in transports:
            delivered = self._push_ntfy(user, title, body, url) or delivered
        return delivered

    @api.model
    def _push_web_push(self, user, title, body, url=None, icon=None):
        """The original web push path, unchanged.

        Kept as its own method so the pre-existing behaviour can be called in
        isolation (tests, or a caller that explicitly wants only web push).
        """
        return super()._push_user_notification(user, title, body, url=url, icon=icon)

    @api.model
    def _push_ntfy(self, user, title, body, url=None):
        """Publish the notification on the user's ntfy topic."""
        try:
            message = self.env['ntfy.message']._publish(
                user,
                title=title,
                body=body,
                click=url,
            )
            return bool(message)
        except Exception:  # noqa: BLE001 — a transport must not break the caller
            _logger.exception('web_ntfy: publish failed for user %s', getattr(user, 'id', '?'))
            return False
