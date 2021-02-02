from odoo import models, fields, api, _
from odoo.exceptions import Warning
import re

class ResGroups(models.Model):

    _inherit = 'res.groups'

    box_ids = fields.One2many('group.dashboard.boxes', 'group_id', "Boxes")
    welcome_dsc = fields.Html("Welcome Description")

    @api.multi
    def write(self, vals):
        res = super(ResGroups, self).write(vals)
        config_obj = self.env['af.dashboard']
        if vals.get('welcome_dsc'):
            for group in self:
                for user in group.users:
                    dashboard = config_obj.search([('user_id', '=', user.id)], limit=1)
                    if dashboard:
                        dashboard.welcome_dsc = ''
                        welcome_dsc = ''
                        for group in user.groups_id:
                            welcome_dsc += group.welcome_dsc if group.welcome_dsc else ''
                        dashboard.welcome_dsc = welcome_dsc

        return res

class GroupBoxes(models.Model):
    _name = 'group.dashboard.boxes'

    name = fields.Html("Title")
    sub_title = fields.Html("Sub title")
    description = fields.Html("Description")
    image = fields.Many2one('fa.class', "Image Class")
    image_class_name = fields.Char(related='image.class_name', store=True)
    action_id = fields.Many2one("ir.actions.act_window", "Action")
    action_url = fields.Char("Action URL", compute="_compute_action_url")
    group_id = fields.Many2one('res.groups', "Group")

    @api.model
    def create(self, vals):
        res = super(GroupBoxes, self).create(vals)
        if res:
            for user in res.group_id.users:
                dashboard = self.env['af.dashboard'].search([('user_id', '=', user.id)], limit=1)
                if dashboard:
                    dashboard.box_ids = [(0, 0, {
                        'af_dashboard_id': dashboard.id,
                        'name': res.name,
                        'sub_title': res.sub_title,
                        'description': res.description,
                        'image': res.image.id if res.image else False,
                        'action_id': res.action_id.id if res.action_id else False,
                        'group_box_id': res.id
                    })]
        return res

    @api.multi
    def write(self, vals):
        res = super(GroupBoxes, self).write(vals)
        for box in self:
            user_boxes = self.env['dashboard.boxes'].search([('group_box_id', '=', box.id)])
            for user_box in user_boxes:
                user_box.write({
                        'name': box.name,
                        'sub_title': box.sub_title,
                        'description': box.description,
                        'image': box.image.id if box.image else False,
                        'action_id': box.action_id.id if box.action_id else False,
                    })
        return res

class Dashboard(models.Model):

    _name = 'af.dashboard'
    _description = "AF Dashboard"

    name = fields.Char("Name")
    user_id = fields.Many2one('res.users', "User")
    firstname = fields.Char(related='user_id.firstname', store=True)
    welcome_msg = fields.Char("Welcome String", default="Welcome")
    welcome_dsc = fields.Html("Welcome Description")
    box_ids = fields.One2many('dashboard.boxes', 'af_dashboard_id')
    group_ids = fields.Many2many('res.groups', related='user_id.groups_id')

    @api.model
    def create(self, vals):
        res = super(Dashboard, self).create(vals)
        if 'from_manual' in self._context:
            raise Warning(_("You can't create manual configuration!"))
        return res

class DashboardBoxes(models.Model):

    _name = 'dashboard.boxes'
    _description = "Dashboard Boxes"
    _rec_name = "user_id"

    af_dashboard_id = fields.Many2one('af.dashboard')
    user_id = fields.Many2one('res.users', related='af_dashboard_id.user_id', store=True)
    name = fields.Html("Title")
    sub_title = fields.Html("Sub title")
    description = fields.Html("Description")
    image = fields.Many2one('fa.class', "Image Class")
    image_class_name = fields.Char(related='image.class_name', store=True)
    action_id = fields.Many2one("ir.actions.act_window", "Action")
    action_url = fields.Char("Action URL", compute="_compute_action_url")
    group_box_id = fields.Many2one("group.dashboard.boxes")
    is_detail = fields.Boolean(compute='_check_is_detail', store=True)

    @api.depends('name', 'sub_title', 'description')
    def _check_is_detail(self):
        for box in self:
            cleanr = re.compile('<.*?>')
            clean_name = re.sub(cleanr, '', box.name)
            clean_sub_title = re.sub(cleanr, '', box.sub_title)
            clean_description = re.sub(cleanr, '', box.description)
            if clean_name or clean_sub_title or clean_description:
                box.is_detail = True
            else:
                box.is_detail = False

    @api.model
    def create(self, vals):
        res = super(DashboardBoxes, self).create(vals)
        if 'from_manual' in self._context:
            raise Warning(_("You can't create manual configuration!"))
        return res

    @api.depends('action_id')
    def _compute_action_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for box in self:
            if box.action_id:
                link = '%s/web#action=%s&model=%s' % (base_url, box.action_id.id, box.action_id.res_model)
                box.action_url = link

class FAClass(models.Model):

    _name = 'fa.class'
    _description = 'FA Class'

    name = fields.Char("Name")
    class_name = fields.Char("Class Name")

class ResUsers(models.Model):

    _inherit = 'res.users'

    @api.model
    def create(self, vals):
        res = super(ResUsers, self).create(vals)
        if res:
            dashboard = self.env['af.dashboard'].sudo().create({
                'name': res.name,
                'user_id': res.id
            })
            if dashboard:
                welcome_dsc = ''
                for group in res.groups_id:
                    welcome_dsc += group.welcome_dsc if group.welcome_dsc else ''
                    for g_box in group.box_ids:
                        dashboard.box_ids = [(0, 0, {
                            'af_dashboard_id': dashboard.id,
                            'name': g_box.name,
                            'sub_title': g_box.sub_title,
                            'description': g_box.description,
                            'image': g_box.image.id if g_box.image else False,
                            'action_id': g_box.action_id.id if g_box.action_id else False,
                            'group_box_id': g_box.id
                        })]
                dashboard.welcome_dsc = welcome_dsc
        return res

    @api.multi
    def write(self, vals):
        res = super(ResUsers, self).write(vals)
        dashboard_obj = self.env['af.dashboard']
        for user in self:
            dashboard = dashboard_obj.search([('user_id', '=', user.id)], limit=1)
            if dashboard:
                dashboard_boxes = dashboard.box_ids.mapped('group_box_id').ids
                dashboard.welcome_dsc = ''
                group_boxes_list = []
                desc = ''
                for group in user.groups_id:
                    desc += group.welcome_dsc if group.welcome_dsc else ''
                    for g_box in group.box_ids:
                        group_boxes_list.append(g_box.id)
                        if g_box.id not in dashboard_boxes:
                            dashboard.box_ids = [(0, 0, {
                                'af_dashboard_id': dashboard.id,
                                'name': g_box.name,
                                'sub_title': g_box.sub_title,
                                'description': g_box.description,
                                'image': g_box.image.id if g_box.image else False,
                                'action_id': g_box.action_id.id if g_box.action_id else False,
                                'group_box_id': g_box.id
                            })]
                dashboard.welcome_dsc = desc
                user_boxes_list = dashboard.box_ids.mapped('group_box_id').ids
                extra_boxes = list(set(user_boxes_list) - set(group_boxes_list))
                for extra_box in extra_boxes:
                    box = self.env['dashboard.boxes'].search([('user_id', '=', user.id),
                                                              ('group_box_id', '=', extra_box)])
                    if box:
                        box.unlink()
        return res