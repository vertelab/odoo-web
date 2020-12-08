from odoo import models, fields

class AccessibilityReport(models.Model):

    _name = "accessibility.report"
    _description = "Accessibility Report"
    _rec_name = 'name_2'

    name = fields.Html("Repor Content")
    name_2 = fields.Char("Name", default="Accessibility Report")