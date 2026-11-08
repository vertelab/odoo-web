# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel Sverige AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestNtfyTransport(TransactionCase):
    """Transport selection and the fan-out contract."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pusher = cls.env['web.pwa.push']
        cls.user = cls.env['res.users'].create({
            'name': 'Ntfy Transport User',
            'login': 'ntfy_transport_user@example.com',
            'email': 'ntfy_transport_user@example.com',
        })
        cls.icp = cls.env['ir.config_parameter'].sudo()

    def _set(self, **params):
        for key, value in params.items():
            self.icp.set_param('web_ntfy.%s' % key, value)
        self.env.invalidate_all()

    def test_no_transports_when_both_disabled(self):
        self._set(enabled='False', transport_web_push='False', transport_ntfy='False')
        self.assertEqual(self.pusher._enabled_transports(), set())

    def test_ntfy_off_leaves_web_push(self):
        self._set(enabled='False', transport_web_push='True', transport_ntfy='True')
        self.assertEqual(self.pusher._enabled_transports(), {'web_push'})

    def test_both_transports(self):
        self._set(enabled='True', transport_web_push='True', transport_ntfy='True')
        self.assertEqual(self.pusher._enabled_transports(), {'web_push', 'ntfy'})

    def test_ntfy_enabled_but_transport_off(self):
        self._set(enabled='True', transport_web_push='True', transport_ntfy='False')
        self.assertEqual(self.pusher._enabled_transports(), {'web_push'})

    def test_ntfy_transport_publishes_message(self):
        self._set(enabled='True')
        self.pusher._push_ntfy(self.user, 'Done', 'The coworker replied.')
        topic = self.env['ntfy.topic']._topic_for_user(self.user)
        messages = self.env['ntfy.message'].search([('topic', '=', topic)])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages.title, 'Done')
        self.assertEqual(messages.body, 'The coworker replied.')

    def test_explicit_transports_bypass_settings(self):
        """An explicit set wins over the server settings."""
        self._set(enabled='True', transport_web_push='False', transport_ntfy='False')
        self.pusher._push_user_notification(
            self.user, 'T', 'B', transports={'ntfy'})
        topic = self.env['ntfy.topic']._topic_for_user(self.user)
        self.assertTrue(self.env['ntfy.message'].search([('topic', '=', topic)]))

    def test_backward_compatible_signature(self):
        """Existing callers pass (user, title, body, url) and get a bool."""
        self._set(enabled='True', transport_web_push='True', transport_ntfy='True')
        result = self.pusher._push_user_notification(
            self.user, 'Title', 'Body', '/ai/chat')
        self.assertIsInstance(result, bool)

    def test_ntfy_failure_does_not_break_caller(self):
        """A transport must never raise into the calling code."""
        self._set(enabled='True')
        # A user without a partner cannot be addressed — _publish returns an
        # empty recordset, and _push_ntfy reports False instead of raising.
        result = self.pusher._push_ntfy(False, 'x', 'y')
        self.assertFalse(result)

    def test_publish_without_user_creates_nothing(self):
        self.assertFalse(self.env['ntfy.message']._publish(False, title='x', body='y'))
