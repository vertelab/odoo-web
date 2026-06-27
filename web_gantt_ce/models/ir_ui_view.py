# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    type = fields.Selection(selection_add=[('gantt', 'Gantt')])

    def _get_view_info(self):
        return {'gantt': {'icon': 'fa fa-tasks'}} | super()._get_view_info()


class IrActionsActWindowView(models.Model):
    _inherit = 'ir.actions.act_window.view'

    view_mode = fields.Selection(selection_add=[
        ('gantt', 'Gantt')
    ], ondelete={'gantt': 'cascade'})
