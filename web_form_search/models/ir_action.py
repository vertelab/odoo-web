# -*- coding: utf-8 -*-
from odoo import fields, models


class ActWindowView(models.Model):
    _inherit = 'ir.actions.act_window.view'

    view_mode = fields.Selection(selection_add=[('form_search', "Form Search"),
                                                ('form_search_tree', "Form Search Tree")
                                                ])


