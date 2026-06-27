# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        result = super().session_info()
        # No MapBox token needed — using OpenStreetMap/Nominatim instead
        if self.env.user._is_internal():
            result.update(map_box_token=False)
        return result
