# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, models
from odoo.osv import expression


class GanttMixin(models.AbstractModel):
    """Server-side support for the ``gantt`` view.

    Any model that should be displayed in a gantt view can inherit from this
    mixin (e.g. ``_inherit = ['res.partner', 'gantt.mixin']``). The model must
    provide the ``date_start``/``date_stop`` fields referenced in the arch.
    """

    _name = 'gantt.mixin'
    _description = 'Gantt Mixin'

    @api.model
    def get_gantt_data(self, domain, groupby, read_specification, limit=None, offset=0,
                       unavailability_fields=None, progress_bar_fields=None,
                       start_date=None, stop_date=None, scale=None):
        """Compute the data required by the gantt view.

        :param list domain: search domain (already restricted to the visible
            time range by the view)
        :param list groupby: list of group-by field names
        :param dict read_specification: fields to read, ``{name: spec}``
        :returns: dict with ``groups`` or ``records``, ``length``,
            ``progress_bars`` and ``unavailabilities``
        """
        unavailability_fields = unavailability_fields or []
        progress_bar_fields = progress_bar_fields or []
        groupby = [groupby] if isinstance(groupby, str) else groupby

        if groupby:
            groups = self._read_group_gantt(
                domain, groupby, read_specification,
                limit=limit, offset=offset,
            )
            record_ids = []
            for group in groups:
                record_ids.extend(group.get('__record_ids') or [])
            records = self._get_gantt_records(
                [('id', 'in', record_ids)], read_specification,
            )
        else:
            records = self._get_gantt_records(
                domain, read_specification, limit=limit, offset=offset,
            )
            # Ungrouped: the view still expects ``groups`` (one row containing
            # all the visible record ids), otherwise no pill would be rendered.
            groups = [{
                '__count': len(records),
                '__record_ids': [record['id'] for record in records],
            }]

        return {
            'groups': groups,
            'records': records,
            'length': self.search_count(domain),
            'progress_bars': self._get_progress_bars(domain, progress_bar_fields),
            'unavailabilities': self._get_unavailabilities(domain, unavailability_fields),
        }

    def _get_gantt_records(self, domain, read_specification, limit=None, offset=0):
        records = []
        fields = list(read_specification or {})
        for record in self.search(domain, limit=limit, offset=offset):
            records.append(record.read(fields=fields)[0])
        return records

    def _read_group_gantt(self, domain, groupby, read_specification, limit=None, offset=0):
        groupby = [groupby] if isinstance(groupby, str) else groupby
        if not groupby or groupby[0] not in self._fields:
            return []
        if not self._fields[groupby[0]].store:
            # computed (non-stored) group-by field: ``read_group`` can only
            # group on stored fields, so fall back to a Python grouping
            return self._read_group_gantt_python(domain, groupby, limit=limit, offset=offset)
        # Non-lazy read_group returns one row per combination of all the
        # group-by fields; each row is extended with the list of record ids
        # belonging to the group (``__record_ids``) as expected by the view.
        groups = self.read_group(
            domain,
            fields=['id:array_agg', '__count'],
            groupby=groupby,
            lazy=False,
            limit=limit,
            offset=offset,
        )
        for group in groups:
            group['__record_ids'] = group.pop('id', [])
        return groups

    def _read_group_gantt_python(self, domain, groupby, limit=None, offset=0):
        """Group the records in Python (fallback for computed group-by fields).

        Produces the same shape as the ``read_group`` path: one row per group
        with the formatted group value and the list of record ids.
        """
        groupby_field = groupby[0]
        field = self._fields[groupby_field]

        grouped = {}
        for record in self.search(domain):
            value = record[groupby_field]
            key = self._gantt_group_key(field, value)
            if key not in grouped:
                grouped[key] = {'_value': value, '__count': 0, '__record_ids': []}
            grouped[key]['__count'] += 1
            grouped[key]['__record_ids'].append(record.id)

        groups = []
        for key, group in grouped.items():
            value = group.pop('_value')
            group[groupby_field] = self._gantt_format_group_value(field, value)
            group['__domain'] = expression.AND([
                domain,
                self._gantt_group_domain(groupby_field, field, value),
            ])
            groups.append(group)

        groups.sort(key=lambda g: g[groupby_field] is False)
        if offset:
            groups = groups[offset:]
        if limit:
            groups = groups[:limit]
        return groups

    def _gantt_group_key(self, field, value):
        if field.type == 'many2one':
            return ('m2o', value.id if value else False)
        if field.type == 'many2many':
            return ('m2m', tuple(value.ids) if value else ())
        if field.type == 'date':
            return ('date', value and value.isoformat())
        if field.type == 'datetime':
            return ('datetime', value and value.isoformat())
        return value

    def _gantt_format_group_value(self, field, value):
        """Format a group value the same way ``read_group`` does."""
        if field.type == 'many2one':
            return (value.id, value.display_name) if value else False
        if field.type == 'many2many':
            return (value.id, value.display_name) if value else False
        if field.type == 'date':
            return value and value.strftime('%Y-%m-%d') or False
        if field.type == 'datetime':
            return value and value.strftime('%Y-%m-%d %H:%M:%S') or False
        return value

    def _gantt_group_domain(self, groupby_field, field, value):
        if field.type == 'many2many':
            if not value:
                return [(groupby_field, 'not any', [])]
            return [(groupby_field, 'in', value.ids)]
        if field.type == 'many2one':
            return [(groupby_field, '=', value.id if value else False)]
        return [(groupby_field, '=', value)]

    def _get_progress_bars(self, domain, progress_bar_fields):
        """Return the progress bar data per record.

        Override this method in concrete models to provide
        ``{field: {res_id: {'value': ..., 'max_value': ...}}}``.
        """
        return {field_name: {} for field_name in progress_bar_fields or []}

    def _get_unavailabilities(self, domain, unavailability_fields):
        """Return the unavailability data per record.

        Override this method in concrete models to provide
        ``{field: {res_id: [{'start': ..., 'stop': ...}]}}``.
        """
        return {field_name: {} for field_name in unavailability_fields or []}

    @api.model
    def web_gantt_reschedule(self, data, reschedule_method, ids, dependency_field,
                             dependency_inverted_field, date_start_field, date_stop_field):
        """Reschedule the given records.

        Kept intentionally simple in this CE port: the schedule values are
        written directly on the records. Models that need dependency-aware
        rescheduling (buffer consumption, etc.) can override this method.
        """
        if not isinstance(ids, (list, tuple)):
            ids = [ids]
        self.browse(ids).write(data)
        return data


class ResPartner(models.Model):
    """Make ``res.partner`` usable in gantt views (demo views)."""

    _name = 'res.partner'
    _inherit = ['res.partner', 'gantt.mixin']
