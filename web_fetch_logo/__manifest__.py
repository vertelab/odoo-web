# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Web: Fetch Logo',
    'summary': 'Fetch company logos from a domain via a tier chain',
    'description': 'Generic company-logo fetcher for Odoo 18 CE. Exposes a '
                   'standalone function (fetch_logo / fetch_logo_b64) and a '
                   'thin mixin (web.fetch.logo.mixin). Tier chain: logo.dev '
                   '(when an API key is configured) -> icon.horse -> Google '
                   'favicon -> HTML scraping. SVG is preserved when the '
                   'source delivers it; scraped SVG is sanitized against '
                   'active content. The logo.dev API key is managed in '
                   'General Settings, near Contacts.',
    'category': 'Hidden',
    'version': '18.0.1.0.1',
    'depends': ['web', 'base_setup'],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'author': 'Vertel AB',
    'license': 'LGPL-3',
}
