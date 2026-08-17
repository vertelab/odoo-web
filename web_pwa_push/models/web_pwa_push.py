# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import json
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class WebPwaPush(models.AbstractModel):
    """Stateless helper för att köa web push till en användares enheter.

    Återanvänder Odoos mail.push-kö + cron (samma maskineri som native
    web push) — icke-blockerande. Används av AI-händelser (coworker klar,
    HITL väntar) och av andra moduler som vill pusha enkla notiser.
    """
    _name = 'web.pwa.push'
    _description = 'Web PWA Push Helper'

    @api.model
    def _push_user_notification(self, user, title, body, url=None, icon=None):
        """Queue a web push to a user's registered devices (non-blocking).

        :param user: res.users-mottagare
        :param title: rubrik i notisen
        :param body: brödtext
        :param url: öppnas vid klick (default '/')
        :return: True om push könades, False annars (inga enheter / inga nycklar)
        """
        user = user.sudo()
        if not user or not user.partner_id:
            return False
        devices = self.env['mail.push.device'].sudo().search(
            [('partner_id', '=', user.partner_id.id)])
        if not devices:
            return False
        icp = self.env['ir.config_parameter'].sudo()
        if not icp.get_param('mail.web_push_vapid_private_key') or \
                not icp.get_param('mail.web_push_vapid_public_key'):
            _logger.warning(
                'web_pwa_push: missing VAPID keys, push to user %s skipped',
                user.id)
            return False
        payload = {'title': title or 'Odoo', 'body': body or '', 'url': url or '/'}
        if icon:
            payload['icon'] = icon
        payload_json = json.dumps(payload, default=str)
        self.env['mail.push'].sudo().create([{
            'mail_push_device_id': device.id,
            'payload': payload_json,
        } for device in devices])
        self.env.ref('mail.ir_cron_web_push_notification')._trigger()
        return True
