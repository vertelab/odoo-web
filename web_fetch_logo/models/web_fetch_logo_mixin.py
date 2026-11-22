# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import models

from odoo.addons.web_fetch_logo.models.logo_fetcher import (
    fetch_logo_b64 as _fetch_logo_b64,
)


class WebFetchLogoMixin(models.AbstractModel):
    """Mixin exposing the logo fetcher as an Odoo method (future use).

    Inherit this mixin on any model that wants a ``fetch_logo_b64`` method
    backed by the standalone function. The logo.dev API key is read from
    ``ir.config_parameter`` (``web_fetch_logo.logo_dev_api_key``), so
    callers do not need to manage the key themselves.
    """

    _name = 'web.fetch.logo.mixin'
    _description = 'Web Fetch Logo Mixin'

    def fetch_logo_b64(self, domain_or_url):
        """Return base64 logo for ``domain_or_url``, or ``None``.

        Uses the environment's ``ir.config_parameter`` for the logo.dev
        API key. Never raises on fetch failures.
        """
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'web_fetch_logo.logo_dev_api_key', '')
        return _fetch_logo_b64(domain_or_url, api_key=api_key)
