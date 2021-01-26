from odoo import models, fields, api, _

class UpdateDashboardConfiguration(models.TransientModel):

    _name = 'update.dashboard.config'
    _description = "Update Dashboard"

    welcome_msg = fields.Char("Welcome String")
    welcome_dsc = fields.Html("Welcome Description")
    group_ids = fields.Many2many("res.groups", "rel_update_dashboax_box_group", "update_dash__id",
                                 "rel_update_dah_group_id", "Groups")

    def upate_data(self):
        config_obj = self.env['af.dashboard']
        for group in self.group_ids:
            for user in group.users:
                config = config_obj.search([('user_id', '=', user.id)], limit=1)
                if config:
                    config.welcome_msg = self.welcome_msg
                    config.welcome_dsc = self.welcome_dsc