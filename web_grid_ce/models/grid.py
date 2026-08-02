# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from datetime import datetime, timedelta

from odoo import api, models


class GridMixin(models.AbstractModel):
    """Server-side support for the ``grid`` view.

    Any model that should be displayed in a grid view can inherit from this
    mixin (e.g. ``_inherit = ['res.partner', 'grid.mixin']``).
    """

    _name = 'grid.mixin'
    _description = 'Grid Mixin'

    @api.model
    def grid_update_cell(self, domain, measure_field_name, diff):
        """Update all records in ``domain`` by adding ``diff`` to the measure.

        :param list domain: search domain
        :param str measure_field_name: name of the measure field
        :param float diff: difference to apply to the measure field
        :returns: ``False`` when the update is done, or an action to open
            (e.g. to let the user confirm the update in a dialog)
        """
        if not self.env.context.get('install_mode'):
            records = self.search(domain)
            for record in records:
                record[measure_field_name] += diff
        return False

    @api.model
    def grid_unavailability(self, start_date, stop_date):
        """Return the unavailable days (week-ends) in the given period.

        :returns: dict mapping dates to ``True`` for unavailable days
        """
        result = {}
        if start_date and stop_date:
            day = datetime.strptime(start_date, '%Y-%m-%d').date()
            stop = datetime.strptime(stop_date, '%Y-%m-%d').date()
            while day <= stop:
                if day.isoweekday() >= 6:
                    result[day] = True
                day += timedelta(days=1)
        return result


class ResPartner(models.Model):
    """Make ``res.partner`` usable in grid views (parity with the other CE views)."""

    _name = 'res.partner'
    _inherit = ['res.partner', 'grid.mixin']
