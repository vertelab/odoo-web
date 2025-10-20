# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.http import request, Controller, route


# 1. Model för SWOT-analys
class SwotAnalysis(models.Model):
    _name = 'swot.analysis'
    _description = 'SWOT Analysis'
    _rec_name = 'name'

    name = fields.Char('Namn', required=True)
    description = fields.Text('Beskrivning')
    
    # SWOT-fält
    strengths = fields.Text('Styrkor (Strengths)', help="Interna positiva faktorer")
    weaknesses = fields.Text('Svagheter (Weaknesses)', help="Interna negativa faktorer")
    opportunities = fields.Text('Möjligheter (Opportunities)', help="Externa positiva faktorer")
    threats = fields.Text('Hot (Threats)', help="Externa negativa faktorer")
    
    # Metadata
    create_date = fields.Datetime('Skapad', readonly=True)
    write_date = fields.Datetime('Uppdaterad', readonly=True)
    user_id = fields.Many2one('res.users', 'Ansvarig', default=lambda self: self.env.user)

