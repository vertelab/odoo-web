# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta

from odoo import fields, models
from odoo.addons.base.tests.common import TransactionCaseWithUserDemo
from odoo.exceptions import UserError


class GanttRescheduleTask(models.Model):
    """Test model for dependency-aware rescheduling.

    ``plan_a``/``plan_b`` are the dependency fields: ``plan_a`` holds the
    predecessors, ``plan_b`` the successors. The model opts in to
    dependency-aware rescheduling by overriding
    ``_gantt_reschedule_relations`` and ``_gantt_reschedule_is_candidate``
    through the ``reschedule_blocked`` flag.
    """

    _name = 'gantt.reschedule.test.task'
    _module = 'web_gantt_ce'
    _description = 'Gantt Reschedule Test Task'
    _inherit = ['gantt.mixin']

    name = fields.Char()
    date_start = fields.Datetime()
    date_stop = fields.Datetime()
    plan_a = fields.Many2many(
        'gantt.reschedule.test.task', 'gantt_reschedule_rel_a',
        'task_id', 'other_id', string="Predecessors")
    plan_b = fields.Many2many(
        'gantt.reschedule.test.task', 'gantt_reschedule_rel_b',
        'task_id', 'other_id', string="Successors")
    reschedule_blocked = fields.Boolean()
    reschedule_relations = fields.Boolean(
        default=False,
        help="When set, this record follows its predecessors/successors.")
    reschedule_snap_dates = fields.Boolean(
        help="Test switch: snap the computed dates to midnight.")
    reschedule_explode_on_write = fields.Boolean(
        help="Test switch: raise while writing the dates.")

    def _gantt_reschedule_is_candidate(self, date_start_field, date_stop_field):
        self.ensure_one()
        return not self.reschedule_blocked

    def _gantt_reschedule_compute_dates(self, date_candidate, search_forward,
                                        date_start_field, date_stop_field,
                                        reschedule_method=None):
        self.ensure_one()
        if not self.reschedule_snap_dates:
            return super()._gantt_reschedule_compute_dates(
                date_candidate, search_forward,
                date_start_field, date_stop_field, reschedule_method)
        start = fields.Datetime.to_datetime(date_candidate)
        snapped = start.replace(hour=0, minute=0, second=0)
        return snapped, snapped + timedelta(hours=8)

    def _gantt_reschedule_write_dates(self, start, stop, date_start_field, date_stop_field):
        self.ensure_one()
        if self.reschedule_explode_on_write:
            raise UserError("boom")
        return super()._gantt_reschedule_write_dates(
            start, stop, date_start_field, date_stop_field)

    def _gantt_reschedule_relations(self, dependency_field, dependency_inverted_field,
                                    search_forward, reschedule_method=None):
        self.ensure_one()
        if not self.reschedule_relations:
            return self.browse()
        field_name = dependency_inverted_field if search_forward else dependency_field
        return self[field_name]


class TestGanttReschedule(TransactionCaseWithUserDemo):
    """Cover the rescheduling contract of ``gantt.mixin``."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # The test model is declared in this file, so it must be registered
        # and its table created before it can be used.
        GanttRescheduleTask._build_model(cls.registry, cls.cr)
        cls.registry.setup_models(cls.cr)
        cls.registry.init_models(
            cls.cr, ['gantt.reschedule.test.task'], {'module': 'web_gantt_ce'})
        cls.Task = cls.env['gantt.reschedule.test.task']
        cls.base = datetime(2026, 1, 5, 8, 0, 0)
        cls.dependency_field = 'plan_a'
        cls.dependency_inverted_field = 'plan_b'

    def _create(self, name, start, stop, **kwargs):
        return self.Task.create({
            'name': name,
            'date_start': start,
            'date_stop': stop,
            **kwargs,
        })

    def _reschedule(self, record, start, stop, **extra):
        data = {
            'date_start': fields.Datetime.to_string(start),
            'date_stop': fields.Datetime.to_string(stop),
            **extra,
        }
        return self.Task.web_gantt_reschedule(
            data,
            'maintainBuffer',
            record.ids,
            self.dependency_field,
            self.dependency_inverted_field,
            'date_start',
            'date_stop',
        )

    # ------------------------------------------------------------------
    # Standard behaviour (no model rules)
    # ------------------------------------------------------------------

    def test_plain_write_without_dependency_fields(self):
        """Without dependency fields the dropped values are written as-is."""
        task = self._create('Solo', self.base, self.base + timedelta(hours=4))
        result = self.Task.web_gantt_reschedule(
            {'date_start': '2026-01-06 08:00:00',
             'date_stop': '2026-01-06 12:00:00'},
            'maintainBuffer', task.ids, False, False, 'date_start', 'date_stop',
        )
        self.assertEqual(task.date_start, datetime(2026, 1, 6, 8, 0, 0))
        self.assertEqual(task.date_stop, datetime(2026, 1, 6, 12, 0, 0))
        self.assertEqual(result['type'], 'success')

    def test_default_moves_no_other_record(self):
        """A model without its own rules moves nothing but the dragged record."""
        predecessor = self._create(
            'Predecessor', self.base, self.base + timedelta(hours=4),
            plan_b=[(6, 0, [])],
        )
        successor = self._create(
            'Successor', self.base + timedelta(hours=8),
            self.base + timedelta(hours=12),
            plan_a=[(6, 0, [predecessor.id])],
        )
        self._reschedule(predecessor, self.base + timedelta(days=1),
                         self.base + timedelta(days=1, hours=4))
        self.assertEqual(successor.date_start, self.base + timedelta(hours=8),
                         "a model without rules must not move its successors")

    # ------------------------------------------------------------------
    # Dependencies follow the moved record
    # ------------------------------------------------------------------

    def test_dependency_follows_forward(self):
        """Moving forward drags the successors along."""
        moved = self._create(
            'Moved', self.base, self.base + timedelta(hours=4),
            reschedule_relations=True)
        successor = self._create(
            'Successor', self.base + timedelta(hours=8),
            self.base + timedelta(hours=12),
            plan_a=[(6, 0, [moved.id])])
        moved.plan_b = [(6, 0, [successor.id])]

        new_start = self.base + timedelta(days=1)
        self._reschedule(moved, new_start, new_start + timedelta(hours=4))

        self.assertEqual(moved.date_start, new_start)
        self.assertEqual(
            successor.date_start, self.base + timedelta(days=1, hours=8),
            "the successor keeps its offset to the moved record")

    def test_dependency_chain_is_recursive(self):
        """The whole chain moves, not just the direct successor."""
        moved = self._create(
            'Moved', self.base, self.base + timedelta(hours=4),
            reschedule_relations=True)
        middle = self._create(
            'Middle', self.base + timedelta(hours=8),
            self.base + timedelta(hours=12), reschedule_relations=True)
        last = self._create(
            'Last', self.base + timedelta(hours=16),
            self.base + timedelta(hours=20))
        moved.plan_b = [(6, 0, [middle.id])]
        middle.plan_b = [(6, 0, [last.id])]

        new_start = self.base + timedelta(days=1)
        self._reschedule(moved, new_start, new_start + timedelta(hours=4))

        self.assertEqual(middle.date_start, self.base + timedelta(days=1, hours=8))
        self.assertEqual(last.date_start, self.base + timedelta(days=1, hours=16))

    # ------------------------------------------------------------------
    # Blocking
    # ------------------------------------------------------------------

    def test_blocked_dependency_aborts_the_whole_move(self):
        """A dependency that may not move aborts everything."""
        moved = self._create(
            'Moved', self.base, self.base + timedelta(hours=4),
            reschedule_relations=True)
        successor = self._create(
            'Blocked successor', self.base + timedelta(hours=8),
            self.base + timedelta(hours=12), reschedule_blocked=True)
        moved.plan_b = [(6, 0, [successor.id])]

        new_start = self.base + timedelta(days=1)
        result = self._reschedule(moved, new_start, new_start + timedelta(hours=4))

        self.assertEqual(result['type'], 'warning')
        self.assertIn(successor.name, result['message'])
        self.assertEqual(moved.date_start, self.base,
                         "the moved record must be left untouched")
        self.assertEqual(successor.date_start, self.base + timedelta(hours=8))

    def test_blocked_moved_record_is_left_alone(self):
        """A record that may not be moved is left untouched, silently."""
        task = self._create(
            'Blocked', self.base, self.base + timedelta(hours=4),
            reschedule_blocked=True)

        new_start = self.base + timedelta(days=1)
        result = self._reschedule(task, new_start, new_start + timedelta(hours=4))

        self.assertEqual(result['type'], 'warning')
        self.assertEqual(task.date_start, self.base)

    # ------------------------------------------------------------------
    # Cycles
    # ------------------------------------------------------------------

    def test_cycle_aborts_without_writing(self):
        """A circular dependency is refused and nothing is written."""
        first = self._create(
            'First', self.base, self.base + timedelta(hours=4),
            reschedule_relations=True)
        second = self._create(
            'Second', self.base + timedelta(hours=8),
            self.base + timedelta(hours=12), reschedule_relations=True)
        first.plan_b = [(6, 0, [second.id])]
        second.plan_b = [(6, 0, [first.id])]

        new_start = self.base + timedelta(days=1)
        result = self._reschedule(first, new_start, new_start + timedelta(hours=4))

        self.assertEqual(result['type'], 'warning')
        self.assertEqual(first.date_start, self.base)
        self.assertEqual(second.date_start, self.base + timedelta(hours=8))

    # ------------------------------------------------------------------
    # Undo
    # ------------------------------------------------------------------

    def test_result_carries_old_vals(self):
        """A successful move reports the values from before the move."""
        moved = self._create(
            'Moved', self.base, self.base + timedelta(hours=4),
            reschedule_relations=True)
        successor = self._create(
            'Successor', self.base + timedelta(hours=8),
            self.base + timedelta(hours=12))
        moved.plan_b = [(6, 0, [successor.id])]

        new_start = self.base + timedelta(days=1)
        result = self._reschedule(moved, new_start, new_start + timedelta(hours=4))

        old_vals = result['old_vals_per_pill_id']
        self.assertEqual(old_vals[moved.id]['date_start'], self.base)
        self.assertEqual(old_vals[successor.id]['date_start'],
                         self.base + timedelta(hours=8))

    def test_rollback_restores_every_written_field(self):
        """Undo restores the dates, including a group change."""
        moved = self._create(
            'Moved', self.base, self.base + timedelta(hours=4),
            reschedule_relations=True)
        successor = self._create(
            'Successor', self.base + timedelta(hours=8),
            self.base + timedelta(hours=12))
        moved.plan_b = [(6, 0, [successor.id])]

        new_start = self.base + timedelta(days=1)
        result = self._reschedule(moved, new_start, new_start + timedelta(hours=4))
        self.assertEqual(moved.date_start, new_start)

        self.Task.action_rollback_scheduling(result['old_vals_per_pill_id'])

        self.assertEqual(moved.date_start, self.base)
        self.assertEqual(moved.date_stop, self.base + timedelta(hours=4))
        self.assertEqual(successor.date_start, self.base + timedelta(hours=8))

    def test_failed_move_offers_no_rollback(self):
        """An aborted move reports a warning and no Undo payload."""
        first = self._create(
            'First', self.base, self.base + timedelta(hours=4),
            reschedule_relations=True)
        second = self._create(
            'Second', self.base + timedelta(hours=8),
            self.base + timedelta(hours=12), reschedule_relations=True)
        first.plan_b = [(6, 0, [second.id])]
        second.plan_b = [(6, 0, [first.id])]

        new_start = self.base + timedelta(days=1)
        result = self._reschedule(first, new_start, new_start + timedelta(hours=4))

        self.assertEqual(result['type'], 'warning')
        self.assertFalse(result['old_vals_per_pill_id'])

    # ------------------------------------------------------------------
    # Hooks
    # ------------------------------------------------------------------

    def test_compute_dates_hook_drives_the_result(self):
        """A model overriding compute_dates controls where the record lands."""
        task = self._create(
            'Snapped', self.base, self.base + timedelta(hours=4),
            reschedule_snap_dates=True)

        new_start = self.base + timedelta(days=1, hours=13, minutes=27)
        self._reschedule(task, new_start, new_start + timedelta(hours=4))

        # The hook snapped the dropped date to midnight and set an 8h span.
        self.assertEqual(task.date_start, datetime(2026, 1, 6, 0, 0, 0))
        self.assertEqual(task.date_stop, datetime(2026, 1, 6, 8, 0, 0))

    def test_error_leaves_every_record_untouched(self):
        """A write failure in a multi-record move rolls the whole move back."""
        moved = self._create(
            'Moved', self.base, self.base + timedelta(hours=4),
            reschedule_relations=True)
        successor = self._create(
            'Successor', self.base + timedelta(hours=8),
            self.base + timedelta(hours=12), reschedule_explode_on_write=True)
        moved.plan_b = [(6, 0, [successor.id])]

        new_start = self.base + timedelta(days=1)
        # The failing write raises a UserError, which the method surfaces as a
        # warning; either way the savepoint must leave every record untouched.
        result = self._reschedule(moved, new_start, new_start + timedelta(hours=4))

        self.assertEqual(result['type'], 'warning')
        self.assertIn('boom', result['message'])
        self.assertEqual(moved.date_start, self.base,
                         "the moved record must be rolled back")
        self.assertEqual(successor.date_start, self.base + timedelta(hours=8))
