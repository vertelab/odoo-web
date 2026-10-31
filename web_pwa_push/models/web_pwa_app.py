# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel Sverige AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class WebPwaApp(models.Model):
    """A PWA app registered with the install hub and manifest router.

    Apps are data, not code: a module that wants its own installable app adds a
    record in its data files instead of patching a hardcoded list. That keeps
    web_pwa_push free of knowledge about every app that uses it.
    """

    _name = "web.pwa.app"
    _description = "PWA App"
    _order = "sequence, key"

    key = fields.Char(
        required=True,
        index=True,
        help="URL key: the manifest is served at /pwa/manifest/<key>.",
    )
    name = fields.Char(
        required=True,
        help="Display name. Empty means: derive it from the company's PWA "
             "branding for this key.",
    )
    description = fields.Char()
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    start_url = fields.Char(
        required=True,
        default="/",
        help="Where the app opens. Defines the app, not the URL it is served from.",
    )
    scope = fields.Char(
        default="/",
        help="Navigation scope. Must contain start_url.",
    )
    display = fields.Selection(
        [
            ("standalone", "Standalone"),
            ("fullscreen", "Fullscreen"),
            ("minimal-ui", "Minimal UI"),
            ("browser", "Browser"),
        ],
        default="standalone",
        required=True,
    )
    icon_url = fields.Char(default="/web_pwa_push/icon192x192.png")
    theme_color = fields.Char(
        help="Empty means: use the company's PWA theme colour.",
    )
    background_color = fields.Char(
        help="Empty means: use the company's PWA background colour.",
    )

    # Which service worker scope the app needs. The service worker is served
    # with Service-Worker-Allowed so a page under /ai/ can register a worker
    # that controls the whole origin.
    service_worker_scope = fields.Char(
        default="/",
        help="Service-Worker-Allowed header value. '/' lets one worker control "
             "the whole origin.",
    )
    install_href = fields.Char(
        help="Where the install card links. Empty means start_url.",
    )

    # Capture: a generic camera entry point. web_pwa_push does not know what a
    # file is - it renders an input and posts to a callback the app names.
    capture_enabled = fields.Boolean(
        help="Show /pwa/capture for this app and accept uploads.",
    )
    capture_model = fields.Char(
        help="Model that receives the upload, e.g. dms.file.",
    )
    capture_method = fields.Char(
        help="Method on capture_model called with the uploaded files.",
    )
    capture_accept = fields.Char(
        default="image/*,application/pdf",
        help="accept attribute of the file input. A technician photographs, "
             "an office worker scans to PDF.",
    )

    _sql_constraints = [
        ("key_uniq", "unique(key)", "The app key must be unique."),
    ]

    @api.constrains("scope", "start_url")
    def _check_scope_contains_start_url(self):
        for record in self:
            scope = record.scope or "/"
            start = record.start_url or "/"
            if not start.startswith(scope):
                raise models.ValidationError(
                    "start_url (%s) must be inside scope (%s)." % (start, scope)
                )

    def get_manifest(self):
        """Return the manifest dict for this app."""
        self.ensure_one()
        company = self.env.company.sudo()
        name = self.name or company.pwa_app_name(self.key)
        return {
            "name": name,
            "short_name": name[:12],
            "start_url": self.start_url or "/",
            "scope": self.scope or "/",
            "display": self.display or "standalone",
            "background_color": self.background_color
            or self._pwa_color("background"),
            "theme_color": self.theme_color or self._pwa_color("theme"),
            "icons": [
                {"src": self.icon_url, "sizes": "192x192", "type": "image/png"},
                {
                    "src": self.icon_url,
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "any maskable",
                },
            ],
        }

    def _pwa_color(self, kind):
        key = "pwa.manifest.%s_color" % kind
        return self.env["ir.config_parameter"].sudo().get_param(key, "#1a1a2e")

    @api.model
    def _get_app(self, key):
        """Look up an active app by key, or an empty recordset."""
        return self.search([("key", "=", key), ("active", "=", True)], limit=1)
