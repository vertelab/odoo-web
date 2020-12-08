from odoo import models, fields

class AccessibilityReport(models.Model):

    _name = "accessibility.report"
    _description = "Accessibility Report"

    name = fields.Html("Name")