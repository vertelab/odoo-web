# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # OpenStreetMap/Nominatim requires no token. EE's MapBox token is removed.
    # Users should respect Nominatim usage policy: max 1 req/s, with caching.
