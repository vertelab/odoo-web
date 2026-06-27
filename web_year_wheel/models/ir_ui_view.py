# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    type = fields.Selection(selection_add=[('year_wheel', 'Year Wheel')])

    def _postprocess_tag_year_wheel(self, node, name_manager, node_info):
        if fnames := node.get('date_field'):
            name_manager.has_field(node, fnames.split('.', 1)[0], node_info)
        if fnames := node.get('color_field'):
            name_manager.has_field(node, fnames.split('.', 1)[0], node_info)
        if fnames := node.get('label_field'):
            name_manager.has_field(node, fnames.split('.', 1)[0], node_info)
        if fnames := node.get('size_field'):
            name_manager.has_field(node, fnames.split('.', 1)[0], node_info)

    def _get_view_info(self):
        return {'year_wheel': {'icon': 'fa fa-circle-o'}} | super()._get_view_info()
