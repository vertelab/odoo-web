# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import json
import logging

from odoo import models

_logger = logging.getLogger(__name__)

# Message types som Odoos nativa web push (_notify_thread_by_web_push →
# _extract_partner_ids_for_notifications) redan hanterar — vi skippar dem
# för att undvika dubbel-push. De täcker i praktiken alla meddelanden som
# går genom mail.thread._notify_thread (comment/notification/email).
_NATIVE_WEB_PUSH_MESSAGE_TYPES = {
    'comment', 'whatsapp_message', 'notification', 'user_notification', 'email',
}


class Notification(models.Model):
    _inherit = 'mail.notification'

    def create(self, vals_list):
        notifications = super().create(vals_list)
        try:
            self._push_inbox_notifications(notifications)
        except Exception:  # pragma: no cover — aldrig blockera notifikationsflödet
            _logger.exception('web_pwa_push: failed to push inbox notifications')
        return notifications

    def _push_inbox_notifications(self, notifications):
        """Skicka web push för inbox-notifikationer som Odoos nativa web
        push inte täcker (direkta mail.notification.create-anrop utanför
        _notify_thread, AI-skapade meddelanden med andra message_types).

        Könar till mail.push + triggar cron:en (samma maskineri som native
        använder vid > MAX_DIRECT_PUSH enheter) — icke-blockerande.
        """
        inbox = notifications.filtered(lambda n: n.notification_type == 'inbox')
        if not inbox:
            return
        icp = self.env['ir.config_parameter'].sudo()
        vapid_private = icp.get_param('mail.web_push_vapid_private_key')
        vapid_public = icp.get_param('mail.web_push_vapid_public_key')
        if not vapid_private or not vapid_public:
            _logger.warning('web_pwa_push: missing VAPID keys, inbox push skipped')
            return

        push_vals = []
        for notif in inbox:
            message = notif.message_id.sudo()
            if not message:
                continue
            if message.message_type in _NATIVE_WEB_PUSH_MESSAGE_TYPES:
                # Native web push hanterar denna typ → skippa (ingen dubbel-push)
                continue
            partner = notif.res_partner_id
            if not partner or (message.author_id and partner == message.author_id):
                continue
            devices = self.env['mail.push.device'].sudo().search(
                [('partner_id', '=', partner.id)])
            if not devices:
                continue
            payload = self.env['mail.thread'].sudo()._notify_by_web_push_prepare_payload(
                message)
            payload['title'] = payload.get('title') or 'Odoo'
            payload_json = json.dumps(payload, default=str)
            push_vals += [{
                'mail_push_device_id': device.id,
                'payload': payload_json,
            } for device in devices]

        if push_vals:
            self.env['mail.push'].sudo().create(push_vals)
            self.env.ref('mail.ir_cron_web_push_notification')._trigger()
