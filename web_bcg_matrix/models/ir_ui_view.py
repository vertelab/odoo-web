# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    type = fields.Selection(selection_add=[('bcg_matrix', 'BCG Matrix')])

    def _postprocess_tag_bcg_matrix(self, node, name_manager, node_info):
        for attr in ('x_field', 'y_field', 'label_field', 'size_field', 'color_field'):
            if fnames := node.get(attr):
                name_manager.has_field(node, fnames.split('.', 1)[0], node_info)

    def _get_view_info(self):
        return {'bcg_matrix': {'icon': 'fa fa-th'}} | super()._get_view_info()
