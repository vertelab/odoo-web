# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel Sverige AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestNtfyTopic(TransactionCase):
    """The topic is derived, stable and never stored on the user."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.topic_model = cls.env['ntfy.topic']
        cls.user_a = cls.env['res.users'].create({
            'name': 'Ntfy Test A',
            'login': 'ntfy_test_a@example.com',
            'email': 'ntfy_test_a@example.com',
        })
        cls.user_b = cls.env['res.users'].create({
            'name': 'Ntfy Test B',
            'login': 'ntfy_test_b@example.com',
            'email': 'ntfy_test_b@example.com',
        })

    def test_topic_is_stable(self):
        """Two calls return the same topic."""
        first = self.topic_model._topic_for_user(self.user_a)
        second = self.topic_model._topic_for_user(self.user_a)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 32)

    def test_topics_differ_per_user(self):
        self.assertNotEqual(
            self.topic_model._topic_for_user(self.user_a),
            self.topic_model._topic_for_user(self.user_b),
        )

    def test_topic_not_stored_on_user(self):
        """No field on res.users holds the topic."""
        topic = self.topic_model._topic_for_user(self.user_a)
        user_fields = self.env['res.users']._fields
        for name, field in user_fields.items():
            if field.type not in ('char', 'text'):
                continue
            value = self.user_a[name]
            self.assertNotEqual(
                value, topic,
                'res.users.%s must not store the topic' % name,
            )

    def test_salt_rotation_changes_topic(self):
        """Rotating the salt re-addresses every user."""
        before = self.topic_model._topic_for_user(self.user_a)
        self.env['ir.config_parameter'].sudo().set_param(
            'web_ntfy.salt', 'a-completely-different-salt-value')
        after = self.topic_model._topic_for_user(self.user_a)
        self.assertNotEqual(before, after)

    def test_resolve_topic_back_to_user(self):
        topic = self.topic_model._topic_for_user(self.user_a)
        self.assertEqual(self.topic_model._user_for_topic(topic), self.user_a)

    def test_unknown_topic_resolves_to_empty(self):
        self.assertFalse(self.topic_model._user_for_topic('doesnotexist123456789012345678'))
