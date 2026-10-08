# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel Sverige AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
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
                       start_date=None, stop_date=None, scale=None, progress_field=None):
        """Compute the data required by the gantt view.

        :param list domain: search domain (already restricted to the visible
            time range by the view)
        :param list groupby: list of group-by field names
        :param dict read_specification: fields to read, ``{name: spec}``
        :param str progress_field: name of the field used to determine whether
            a record is "done" (arch ``progress`` attribute)
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
            'progress_bars': self._get_progress_bars(
                domain, progress_bar_fields, progress_field,
                start_date, stop_date,
            ),
            'unavailabilities': self._get_unavailabilities(
                domain, unavailability_fields, start_date, stop_date,
            ),
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

    def _get_progress_bars(self, domain, progress_bar_fields, progress_field=None,
                           start_date=None, stop_date=None):
        """Compute the progress bar data per group.

        For each group-by field listed in ``progress_bar_fields`` (a m2o/m2m
        field), returns ``{field: {res_id: {'value': ..., 'max_value': ...}}}``.

        The computation is delegated to the model's ``_gantt_progress_bar``
        hook, mirroring Odoo Enterprise. Models with a domain-specific
        progress bar (e.g. planned hours per workcenter) override that hook.
        """
        progress_bars = {}
        if not start_date or not stop_date:
            return {field_name: {} for field_name in progress_bar_fields or []}
        start = fields.Datetime.from_string(start_date)
        stop = fields.Datetime.from_string(stop_date)
        for field_name in progress_bar_fields or []:
            field = self._fields.get(field_name)
            if not field or field.type not in ('many2one', 'many2many'):
                continue
            res_ids = set()
            for record in self.search(domain):
                if field.type == 'many2one':
                    if record[field_name]:
                        res_ids.add(record[field_name].id)
                else:
                    res_ids.update(record[field_name].ids)
            progress_bars[field_name] = self._gantt_progress_bar(
                field_name, sorted(res_ids), start, stop,
            )
        return progress_bars

    @api.model
    def _gantt_progress_bar(self, field, res_ids, start, stop):
        """Default progress bar: count records per group.

        ``max_value`` is the number of records in the group, ``value`` the
        number of records whose ``progress`` field is set. Override in a
        model that needs a different measure (e.g. planned hours).

        :param str field: the group-by field the progress bar applies to
        :param list[int] res_ids: ids of the groups to compute the bar for
        :param datetime start: start of the visible range
        :param datetime stop: end of the visible range
        :returns: ``{res_id: {'value': ..., 'max_value': ...}}``
        """
        progress_bars = {}
        for res_id in res_ids:
            progress_bars[res_id] = {'value': 0, 'max_value': 0}
        return progress_bars

    def _get_unavailabilities(self, domain, unavailability_fields, start_date=None, stop_date=None):
        """Compute the unavailability periods per group.

        For each group-by field (m2o/m2m) the related records are resolved to
        a resource (``resource.resource`` via ``resource_id`` when present) and
        their calendar unavailability intervals in the visible range are
        returned as ``{field: {res_id: [{'start': ..., 'stop': ...}]}}``.
        """
        unavailabilities = {}
        if not start_date or not stop_date:
            return {field_name: {} for field_name in unavailability_fields or []}
        for field_name in unavailability_fields or []:
            unavailabilities[field_name] = {}
            field = self._fields.get(field_name)
            if not field or field.type not in ('many2one', 'many2many'):
                continue
            related = self.env[field.comodel_name]
            for record in self.search(domain):
                related |= record[field_name]
            unavailabilities[field_name] = self._get_resource_unavailabilities(
                related, start_date, stop_date,
            )
        return unavailabilities

    def _get_resource_unavailabilities(self, related, start_date, stop_date):
        """Return ``{res_id: [{'start': ..., 'stop': ...}]}`` for the resources
        linked to the given records (through ``resource_id``)."""
        result = {}
        if not related or 'resource_id' not in related._fields:
            return result
        resources = related.resource_id
        if not resources or not hasattr(resources, '_get_unavailable_intervals'):
            return result
        try:
            start = fields.Datetime.from_string(start_date)
            stop = fields.Datetime.from_string(stop_date)
            mapping = resources._get_unavailable_intervals(start, stop)
        except Exception:
            return result
        for record in related:
            intervals = mapping.get(record.resource_id.id)
            if intervals:
                result[record.id] = [{
                    'start': self._gantt_serialize_datetime(interval[0]),
                    'stop': self._gantt_serialize_datetime(interval[1]),
                } for interval in intervals]
        return result

    @staticmethod
    def _gantt_serialize_datetime(dt):
        from datetime import timezone
        if dt.tzinfo:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt.strftime('%Y-%m-%d %H:%M:%S')

    # ------------------------------------------------------------------
    # Rescheduling hooks
    #
    # ``web_gantt_reschedule`` drives the reschedule and delegates every
    # decision to the hooks below. A model opts in to dependency-aware
    # rescheduling by overriding ``_gantt_reschedule_relations``; the
    # defaults reproduce the historical behaviour (write the dropped
    # values, move nothing else).
    # ------------------------------------------------------------------

    def _gantt_reschedule_is_candidate(self, date_start_field, date_stop_field):
        """Return whether ``self`` may be rescheduled.

        Called for the dragged record and for every record reached while
        following dependencies. Returning ``False`` for the dragged record
        leaves it untouched; returning ``False`` for a dependency aborts
        the whole move.

        :return: bool
        """
        self.ensure_one()
        return True

    def _gantt_reschedule_compute_dates(self, date_candidate, search_forward,
                                        date_start_field, date_stop_field,
                                        reschedule_method=None):
        """Compute the new ``(start, stop)`` for ``self``.

        :param date_candidate: the date the record should be scheduled
            around — for the dragged record the dropped date, for a
            dependency the date derived from its predecessor.
        :param search_forward: ``True`` when the move goes later in time.
        :param reschedule_method: ``'maintainBuffer'`` or ``'consumeBuffer'``.
        :return: ``(start, stop)`` as naive UTC datetimes.
        """
        self.ensure_one()
        candidate = fields.Datetime.to_datetime(date_candidate)
        start = fields.Datetime.to_datetime(self[date_start_field]) if self[date_start_field] else candidate
        stop = fields.Datetime.to_datetime(self[date_stop_field]) if self[date_stop_field] else candidate
        duration = stop - start
        if search_forward:
            return candidate, candidate + duration
        return candidate - duration, candidate

    def _gantt_reschedule_write_dates(self, start, stop, date_start_field, date_stop_field):
        """Write the computed dates on ``self``.

        Override to write through a different mechanism (a wizard, a
        related record, ...). The default is a plain ``write``.
        """
        self.ensure_one()
        self.write({date_start_field: start, date_stop_field: stop})

    def _gantt_reschedule_relations(self, dependency_field, dependency_inverted_field,
                                    search_forward, reschedule_method=None):
        """Return the records that must follow ``self`` when it moves.

        The default returns nothing: a model without its own rules moves
        only the record the user dragged. Override to opt in, typically by
        reading one of the two dependency fields:

        * moving forward, follow ``dependency_inverted_field`` (the records
          that depend on this one);
        * moving backward, follow ``dependency_field`` (the records this one
          depends on).

        :return: recordset of the same model.
        """
        self.ensure_one()
        return self.browse()

    @api.model
    def _gantt_reschedule_old_vals(self, record, data):
        """Snapshot the current values of the fields ``data`` is about to write.

        Used to build ``old_vals_per_pill_id`` so the UI can offer an Undo.
        """
        old_vals = {}
        for field_name in data:
            if field_name not in record._fields:
                continue
            field = record._fields[field_name]
            value = record[field_name]
            if field.type in ('many2many', 'one2many'):
                old_vals[field_name] = value.ids or False
            elif field.type == 'many2one':
                old_vals[field_name] = value.id or False
            else:
                old_vals[field_name] = value
        return old_vals

    @api.model
    def _gantt_reschedule_collect(self, moved, dependency_field, dependency_inverted_field,
                                  search_forward, reschedule_method, date_start_field,
                                  date_stop_field):
        """Collect the records to move, in dependency order.

        Depth-first traversal of ``_gantt_reschedule_relations``, braked by
        ``_gantt_reschedule_is_candidate``. Raises ``UserError`` on a cycle
        or on a dependency that may not be moved.

        :return: ``(ordered, seen)`` where ``ordered`` lists the records to
            move after ``moved`` and ``seen`` is the set of ids already
            handled (including ``moved``).
        """
        ordered = []
        seen = set(moved.ids)
        # Records currently on the traversal stack, to detect cycles.
        on_stack = set(moved.ids)

        def visit(record):
            relations = record._gantt_reschedule_relations(
                dependency_field, dependency_inverted_field,
                search_forward, reschedule_method,
            )
            for relation in relations:
                if relation.id in on_stack:
                    raise UserError(_(
                        "Cannot reschedule: the dependencies form a cycle "
                        "(reached %(name)s again).",
                        name=relation.display_name,
                    ))
                if relation.id in seen:
                    continue
                if not relation._gantt_reschedule_is_candidate(date_start_field, date_stop_field):
                    raise UserError(_(
                        "Cannot reschedule: %(name)s depends on the moved "
                        "record but may not be moved.",
                        name=relation.display_name,
                    ))
                seen.add(relation.id)
                on_stack.add(relation.id)
                visit(relation)
                on_stack.discard(relation.id)
                ordered.append(relation)

        for record in moved:
            visit(record)
        return ordered, seen
    @api.model
    def web_gantt_reschedule(self, data, reschedule_method, ids, dependency_field,
                             dependency_inverted_field, date_start_field, date_stop_field):
        """Reschedule the given records, following declared dependencies.

        Every record the move touches — the dragged one and the dependencies
        reached through ``_gantt_reschedule_relations`` — goes through
        ``_gantt_reschedule_compute_dates``. All dates are computed before
        anything is written, and the writes happen in a savepoint, so a
        failure leaves every record untouched.

        :return: ``{'type', 'message', 'old_vals_per_pill_id'}`` — the shape
            ``gantt_renderer.js`` expects, including the Undo payload.
        """
        if not isinstance(ids, (list, tuple)):
            ids = [ids]
        moved = self.browse(ids).exists()
        if not moved:
            return {'type': 'warning', 'message': _("No record to reschedule."),
                    'old_vals_per_pill_id': {}}

        # Snapshot before anything is written, so Undo can restore it.
        old_vals_per_pill_id = {
            record.id: self._gantt_reschedule_old_vals(record, data)
            for record in moved
        }

        if not (dependency_field and dependency_inverted_field):
            # No dependency information in the arch: plain write, as before.
            moved.write(data)
            return {
                'type': 'success',
                'message': _("The records have been rescheduled."),
                'old_vals_per_pill_id': old_vals_per_pill_id,
            }

        try:
            # --- Phase 1: decide, without writing anything ----------------
            for record in moved:
                if not record._gantt_reschedule_is_candidate(date_start_field, date_stop_field):
                    return {
                        'type': 'warning',
                        'message': _("%(name)s may not be rescheduled.",
                                     name=record.display_name),
                        'old_vals_per_pill_id': {},
                    }

            search_forward = True
            if date_start_field in data and moved[date_start_field]:
                search_forward = (
                    fields.Datetime.to_datetime(data[date_start_field])
                    >= fields.Datetime.to_datetime(moved[date_start_field])
                )

            ordered, _seen = self._gantt_reschedule_collect(
                moved, dependency_field, dependency_inverted_field,
                search_forward, reschedule_method,
                date_start_field, date_stop_field,
            )

            # The dragged record is anchored on the date the user dropped it;
            # the dependencies keep their offset to it. Both go through
            # ``_gantt_reschedule_compute_dates`` so a model can constrain
            # every date, not just the ones it drags along.
            dropped_start = fields.Datetime.to_datetime(data[date_start_field])
            delta = dropped_start - fields.Datetime.to_datetime(moved[0][date_start_field])

            plan = []
            for record in moved:
                new_start, new_stop = record._gantt_reschedule_compute_dates(
                    dropped_start, search_forward, date_start_field,
                    date_stop_field, reschedule_method,
                )
                # Anything else the drop carried (grouped-by fields) is kept.
                vals = {key: value for key, value in data.items()
                        if key not in (date_start_field, date_stop_field)}
                vals[date_start_field] = new_start
                vals[date_stop_field] = new_stop
                plan.append((record, vals))

            for record in ordered:
                old_start = fields.Datetime.to_datetime(record[date_start_field])
                candidate = old_start + delta
                new_start, new_stop = record._gantt_reschedule_compute_dates(
                    candidate, search_forward, date_start_field, date_stop_field,
                    reschedule_method,
                )
                plan.append((record, {date_start_field: new_start, date_stop_field: new_stop}))

            # Snapshot the dependencies before any write, for Undo.
            for record, vals in plan:
                old_vals_per_pill_id.setdefault(
                    record.id, self._gantt_reschedule_old_vals(record, vals))

            # --- Phase 2: write, atomically -------------------------------
            with self.env.cr.savepoint():
                for record, vals in plan:
                    if record in moved:
                        record.write(vals)
                    else:
                        record._gantt_reschedule_write_dates(
                            vals[date_start_field], vals[date_stop_field],
                            date_start_field, date_stop_field,
                        )

        except UserError as error:
            return {
                'type': 'warning',
                'message': error.args[0],
                'old_vals_per_pill_id': {},
            }

        return {
            'type': 'success',
            'message': _("The records have been rescheduled."),
            'old_vals_per_pill_id': old_vals_per_pill_id,
        }

    @api.model
    def action_rollback_scheduling(self, old_vals_per_pill_id):
        """Restore the values captured before a reschedule (the Undo button)."""
        for record in self.browse([int(key) for key in old_vals_per_pill_id]):
            vals = old_vals_per_pill_id.get(str(record.id)) or \
                old_vals_per_pill_id.get(record.id)
            if vals and record.exists():
                record.write(vals)


class ResPartner(models.Model):
    """Make ``res.partner`` usable in gantt views (demo views)."""

    _name = 'res.partner'
    _inherit = ['res.partner', 'gantt.mixin']
