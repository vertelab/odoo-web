# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel Sverige AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestNtfyMessage(TransactionCase):
    """Publishing, serialisation and retention."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.message_model = cls.env['ntfy.message']
        cls.user = cls.env['res.users'].create({
            'name': 'Ntfy Msg User',
            'login': 'ntfy_msg_user@example.com',
            'email': 'ntfy_msg_user@example.com',
        })

    def test_publish_creates_message_on_user_topic(self):
        message = self.message_model._publish(
            self.user, title='Hello', body='World', priority='high')
        self.assertTrue(message)
        expected = self.env['ntfy.topic']._topic_for_user(self.user)
        self.assertEqual(message.topic, expected)
        self.assertEqual(message.user_id, self.user)
        self.assertEqual(message.priority, 'high')

    def test_json_shape_matches_ntfy_contract(self):
        message = self.message_model._publish(
            self.user, title='T', body='B', priority='high',
            tags='warning,skull', click='https://example.com')
        data = message._to_ntfy_json()
        self.assertEqual(data['id'], message.message_id)
        self.assertEqual(data['event'], 'message')
        self.assertEqual(data['title'], 'T')
        self.assertEqual(data['message'], 'B')
        self.assertEqual(data['priority'], 4)
        self.assertEqual(data['tags'], ['warning', 'skull'])
        self.assertEqual(data['click'], 'https://example.com')
        self.assertIsInstance(data['time'], int)

    def test_default_priority_omitted_from_json(self):
        """ntfy omits priority 3; sending it would be noise."""
        message = self.message_model._publish(self.user, title='T', body='B')
        self.assertNotIn('priority', message._to_ntfy_json())

    def test_priority_capped_by_setting(self):
        self.env['ir.config_parameter'].sudo().set_param('web_ntfy.max_priority', 'low')
        message = self.message_model._publish(
            self.user, title='T', body='B', priority='max')
        self.assertEqual(message.priority, 'low')

    def test_since_all_returns_everything(self):
        self.message_model._publish(self.user, title='one', body='1')
        self.message_model._publish(self.user, title='two', body='2')
        topic = self.env['ntfy.topic']._topic_for_user(self.user)
        messages = self.message_model._since(topic, 'all')
        self.assertEqual(len(messages), 2)

    def test_since_message_id_returns_later_only(self):
        first = self.message_model._publish(self.user, title='one', body='1')
        second = self.message_model._publish(self.user, title='two', body='2')
        topic = self.env['ntfy.topic']._topic_for_user(self.user)
        messages = self.message_model._since(topic, first.message_id)
        self.assertEqual(messages, second)

    def test_since_empty_returns_nothing(self):
        """No `since` means 'from now on' — not 'everything'."""
        self.message_model._publish(self.user, title='one', body='1')
        topic = self.env['ntfy.topic']._topic_for_user(self.user)
        self.assertFalse(self.message_model._since(topic, None))

    def test_retention_deletes_only_delivered_and_old(self):
        old_delivered = self.message_model._publish(self.user, title='old', body='x')
        old_undelivered = self.message_model._publish(self.user, title='old2', body='y')
        fresh = self.message_model._publish(self.user, title='new', body='z')
        stale_date = fields.Datetime.subtract(fields.Datetime.now(), days=30)
        old_delivered.write({'delivered': True})
        self.env.cr.execute(
            'UPDATE ntfy_message SET create_date = %s WHERE id IN %s',
            (stale_date, tuple((old_delivered + old_undelivered).ids)),
        )
        self.env.invalidate_all()
        self.env['ir.config_parameter'].sudo().set_param('web_ntfy.retention_days', '7')
        self.message_model._cron_retention()
        self.assertFalse(old_delivered.exists(), 'delivered+old must be deleted')
        self.assertTrue(old_undelivered.exists(), 'undelivered must be kept')
        self.assertTrue(fresh.exists(), 'fresh must be kept')
