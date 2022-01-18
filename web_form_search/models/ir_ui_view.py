# -*- coding: utf-8 -*-
from odoo import fields, models


class View(models.Model):
    _inherit = 'ir.ui.view'

    type = fields.Selection(selection_add=[('form_search', "Form Search"), ('form_search_tree', "Form Search Tree")])