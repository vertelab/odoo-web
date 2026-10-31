# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel Sverige AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import json

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestWebPwaApp(TransactionCase):
    """The web.pwa.app registry and the manifest router built on it."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.App = cls.env["web.pwa.app"]
        cls.ai_chat = cls.App._get_app("ai-chat")
        cls.odoo_app = cls.App._get_app("odoo")

    def test_seeded_apps_exist(self):
        """The two apps that used to be hardcoded are seeded as data."""
        self.assertTrue(self.ai_chat, "ai-chat must be seeded")
        self.assertTrue(self.odoo_app, "odoo must be seeded")
        self.assertEqual(self.ai_chat.start_url, "/ai/chat")
        self.assertEqual(self.ai_chat.scope, "/ai/")

    def test_manifest_ai_chat_unchanged(self):
        """The chat manifest keeps the shape devices already installed.

        Regression guard: /pwa/manifest/ai-chat is live. If start_url, scope
        or display change, an installed app loses its identity.
        """
        manifest = self.ai_chat.get_manifest()
        self.assertEqual(manifest["start_url"], "/ai/chat")
        self.assertEqual(manifest["scope"], "/ai/")
        self.assertEqual(manifest["display"], "standalone")
        self.assertIn("icons", manifest)
        self.assertEqual(len(manifest["icons"]), 2)

    def test_manifest_odoo(self):
        """The backend app opens /odoo with a root scope."""
        manifest = self.odoo_app.get_manifest()
        self.assertEqual(manifest["start_url"], "/odoo")
        self.assertEqual(manifest["scope"], "/")

    def test_new_app_gets_manifest_without_code_change(self):
        """A module can add an app as data and get a manifest for free."""
        app = self.App.create(
            {
                "key": "dms-capture",
                "name": "DMS Capture",
                "start_url": "/dms/capture",
                "scope": "/dms/",
                "capture_enabled": True,
                "capture_model": "dms.file",
                "capture_method": "pwa_capture_store",
            }
        )
        manifest = app.get_manifest()
        self.assertEqual(manifest["name"], "DMS Capture")
        self.assertEqual(manifest["start_url"], "/dms/capture")
        self.assertEqual(manifest["scope"], "/dms/")

    def test_scope_must_contain_start_url(self):
        """A start_url outside its scope is rejected."""
        from odoo.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            self.App.create(
                {
                    "key": "bad-app",
                    "name": "Bad",
                    "start_url": "/elsewhere",
                    "scope": "/dms/",
                }
            )

    def test_key_is_unique(self):
        """Two apps cannot share a key."""
        from psycopg2 import IntegrityError

        from odoo.tools import mute_logger

        with mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError):
            self.App.create(
                {
                    "key": "ai-chat",
                    "name": "Duplicate",
                    "start_url": "/ai/chat",
                    "scope": "/ai/",
                }
            )
            self.env.flush_all()

    def test_pwa_app_name_reads_registry(self):
        """pwa_app_name() resolves a registered app's name."""
        app = self.App.create(
            {
                "key": "custom-app",
                "name": "Custom Name",
                "start_url": "/custom",
                "scope": "/",
            }
        )
        self.assertEqual(self.env.company.pwa_app_name("custom-app"), "Custom Name")
        self.assertTrue(app)

    def test_pwa_app_name_keeps_chat_default(self):
        """The chat keeps its 'AI <company>' default when no name is set."""
        name = self.env.company.pwa_app_name("chat")
        self.assertTrue(name.startswith("AI ") or name == "AI Chat")

    def test_capture_accept_default(self):
        """Capture accepts images and PDF by default."""
        app = self.App.create(
            {
                "key": "capture-default",
                "name": "Capture",
                "start_url": "/c",
                "scope": "/",
            }
        )
        self.assertEqual(app.capture_accept, "image/*,application/pdf")

    def test_install_hub_reads_registry(self):
        """The install hub is driven by the registry, not a hardcoded list.

        Checked at the data level: the controller builds its cards from these
        records, so an app added as data appears in the hub without a code
        change. The rendered page is covered by the HTTP tests in
        test_pwa_push.
        """
        apps = self.App.search([("active", "=", True)])
        keys = apps.mapped("key")
        self.assertIn("ai-chat", keys)
        self.assertIn("odoo", keys)
        for app in apps:
            self.assertTrue(app.start_url, "%s has no start_url" % app.key)
            self.assertTrue(
                app.install_href or app.start_url,
                "%s has no install target" % app.key,
            )
