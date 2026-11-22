# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import base64
import json

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.base.tests.common import HttpCaseWithUserDemo


def _fake_keys():
    return json.dumps({
        'p256dh': base64.urlsafe_b64encode(b'x' * 65).decode(),
        'auth': base64.urlsafe_b64encode(b'y' * 16).decode(),
    })


@tagged('-at_install', 'post_install')
class TestWebPwaPushRoutes(HttpCaseWithUserDemo):
    """Routes under /pwa/ — manifest, SW (headers + push-listener), VAPID."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env['ir.config_parameter'].sudo().set_param(
            'web_pwa_push.pwa_app_name', 'AI ACME AB')

    def test_manifest_ai_chat(self):
        response = self.url_open('/pwa/manifest/ai-chat')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/manifest+json')
        data = response.json()
        self.assertEqual(data['start_url'], '/ai/chat')
        self.assertEqual(data['scope'], '/ai/')
        self.assertEqual(data['display'], 'standalone')
        self.assertEqual(data['name'], 'AI ACME AB')
        sizes = [i['sizes'] for i in data['icons']]
        self.assertIn('192x192', sizes)
        self.assertIn('512x512', sizes)

    def test_sw_headers_and_push_listener(self):
        response = self.url_open('/pwa/sw.js')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'text/javascript')
        self.assertEqual(response.headers.get('Service-Worker-Allowed'), '/ai/')
        body = response.text
        self.assertIn("addEventListener('push'", body)
        self.assertIn("addEventListener('pushsubscriptionchange'", body)
        # pass-through: ingen cache
        self.assertIn("addEventListener('fetch'", body)
        self.assertNotIn('caches.open', body)

    def test_vapid_public_key_route(self):
        response = self.url_open('/pwa/vapid-public-key')
        self.assertEqual(response.status_code, 200)
        key = response.json().get('vapid_public_key')
        self.assertTrue(key)
        icp = self.env['ir.config_parameter'].sudo()
        self.assertEqual(icp.get_param('mail.web_push_vapid_public_key'), key)


@tagged('-at_install', 'post_install')
class TestWebPwaPushSettings(TransactionCase):

    def test_generate_vapid_keys(self):
        settings = self.env['res.config.settings'].create({})
        settings.generate_vapid_keys()
        self.assertTrue(settings.pwa_vapid_private_key)
        self.assertTrue(settings.pwa_vapid_public_key)
        # base64url utan padding
        self.assertNotIn('=', settings.pwa_vapid_private_key)
        settings.execute()
        icp = self.env['ir.config_parameter'].sudo()
        self.assertEqual(
            icp.get_param('mail.web_push_vapid_private_key'),
            settings.pwa_vapid_private_key)
        self.assertEqual(
            icp.get_param('mail.web_push_vapid_public_key'),
            settings.pwa_vapid_public_key)

    def test_default_name_chain(self):
        company = self.env['res.company'].create({'name': 'ACME AB'})
        icp = self.env['ir.config_parameter'].sudo()
        icp.set_param('web_pwa_push.pwa_app_name', '')
        self.assertEqual(company.pwa_app_name('chat'), 'AI ACME AB')
        self.assertEqual(company.pwa_app_name('backend'), 'ACME AB')
        icp.set_param('web_pwa_push.pwa_app_name', 'Min App')
        self.assertEqual(company.pwa_app_name('chat'), 'Min App')

    def test_logo_fallback_generates_attachments(self):
        """Utan uppladdad ikon men med företagslogga → attachments genereras
        från loggan (inkl. apple-touch 180)."""
        import base64
        from odoo.tools import file_open
        with file_open('web_pwa_push/static/description/icon.png', 'rb') as f:
            png = f.read()
        company = self.env['res.company'].create({
            'name': 'ACME AB',
            'logo': base64.b64encode(png),
        })
        settings = self.env['res.config.settings'].create({})
        settings.company_id = company
        settings.set_values()
        attachments = self.env['ir.attachment'].sudo().search(
            [('url', 'like', '/web_pwa_push/icon')])
        urls = attachments.mapped('url')
        self.assertIn('/web_pwa_push/icon180x180.png', urls)
        self.assertIn('/web_pwa_push/icon512x512.png', urls)


@tagged('-at_install', 'post_install')
class TestWebPwaPushInbox(TransactionCase):
    """Hook på mail.notification.create — könar push för icke-nativa typer."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        icp = cls.env['ir.config_parameter'].sudo()
        icp.set_param('mail.web_push_vapid_private_key', 'priv')
        icp.set_param('mail.web_push_vapid_public_key', 'pub')
        cls.partner = cls.env['res.partner'].create({'name': 'Bob'})
        cls.device = cls.env['mail.push.device'].create({
            'partner_id': cls.partner.id,
            'endpoint': 'https://push.example.com/endpoint',
            'keys': _fake_keys(),
        })
        cls.author = cls.env['res.partner'].create({'name': 'Alice'})

    def _make_notification(self, message_type):
        message = self.env['mail.message'].create({
            'message_type': message_type,
            'author_id': self.author.id,
            'body': 'test body',
            'model': 'res.partner',
            'res_id': self.partner.id,
        })
        before = self.env['mail.push'].sudo().search_count([])
        self.env['mail.notification'].create({
            'message_id': message.id,
            'res_partner_id': self.partner.id,
            'notification_type': 'inbox',
            'is_read': False,
        })
        return self.env['mail.push'].sudo().search_count([]) - before

    def test_non_native_message_queues_push(self):
        # message_type 'log' ligger utanför _NATIVE_WEB_PUSH_MESSAGE_TYPES
        self.assertGreater(self._make_notification('log'), 0)

    def test_native_message_type_skipped(self):
        # 'comment' hanteras av Odoos nativa web push → ingen dubbel-push
        self.assertEqual(self._make_notification('comment'), 0)

    def test_missing_vapid_keys_no_crash(self):
        icp = self.env['ir.config_parameter'].sudo()
        icp.set_param('mail.web_push_vapid_private_key', '')
        icp.set_param('mail.web_push_vapid_public_key', '')
        # ska inte kasta, inte könas
        self.assertEqual(self._make_notification('log'), 0)
