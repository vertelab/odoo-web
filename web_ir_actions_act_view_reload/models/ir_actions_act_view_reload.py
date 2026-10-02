# Copyright 2017 - 2018 Modoolar <info@modoolar.com>
# Copyright 2018 Brainbean Apps
# Copyright 2020 CorporateHub (https://corporatehub.eu)
# License LGPLv3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo import fields, models


class IrActionsActViewReload(models.Model):
    _name = "ir.actions.act_view_reload"
    _description = "View Reload"
    _inherit = "ir.actions.actions"
    # Odoo 18 stores all ir.actions.* in the shared ir_actions table (same as
    # ir.actions.act_multi). Without this the ORM would create a new table.
    _table = "ir_actions"

    type = fields.Char(default="ir.actions.act_view_reload")

    def _get_readable_fields(self):
        return super()._get_readable_fields() | {"type"}
