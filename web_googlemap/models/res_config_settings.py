from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    googlemap_api_key = fields.Char(
        string='Google Maps API Key',
        config_parameter='web_googlemap.api_key',
    )
