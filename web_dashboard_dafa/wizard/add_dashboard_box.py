from odoo import models, fields, api, _

class AddDashboardBox(models.TransientModel):

    _name = 'add.dashboard.box'
    _description = "Add Dashboard Boxes"

    name = fields.Html("Title")
    sub_title = fields.Html("Sub title")
    description = fields.Html("Description")
    image = fields.Many2one("fa.class", "Image Class")
    group_ids = fields.Many2many("res.groups", "rel_add_dashboax_box_group", "add_dash__id",
                                 "rel_add_dah_group_id", "Groups")
    action_id = fields.Many2one("ir.actions.act_window", "Action")
    action_url = fields.Char("Action URL", compute="_compute_action_url")

    def add_boxes(self):
        for group in self.group_ids:
            group.box_ids = [(0, 0, {
                'name': self.name,
                'sub_title': self.sub_title,
                'description': self.description,
                'image': self.image,
                'action_id': self.action_id if self.action_id.id else False,
                'action_url': self.action_url
            })]

    @api.depends('action_id')
    def _compute_action_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for box in self:
            if box.action_id:
                link = '%s/web#action=%s&model=%s' % (base_url, box.action_id.id, box.action_id.res_model)
                box.action_url = link