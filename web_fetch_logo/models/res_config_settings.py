# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    web_fetch_logo_logo_dev_api_key = fields.Char(
        'logo.dev API-nyckel',
        config_parameter='web_fetch_logo.logo_dev_api_key',
        groups='base.group_system',
        help='API-nyckel för logo.dev (https://logo.dev, gratis nivå). När '
             'nyckeln är satt används logo.dev som första källa i '
             'logo-hämtningskedjan (logo.dev -> icon.horse -> Google -> '
             'scraping); utan nyckel startar kedjan på icon.horse.')
