# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from datetime import date

from babel.dates import format_date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.osv import expression
from odoo.tools.misc import get_lang


class CohortMixin(models.AbstractModel):
    """Server-side support for the ``cohort`` view.

    Any model that should be displayed in a cohort view can inherit from this
    mixin (e.g. ``_inherit = ['res.partner', 'cohort.mixin']``). The model must
    provide the ``date_start``/``date_stop`` fields referenced in the arch.
    """

    _name = 'cohort.mixin'
    _description = 'Cohort Mixin'

    _cohort_display_formats = {
        'day': 'dd MM yyyy',
        'week': 'WW kkkk',
        'month': 'MMMM yyyy',
        'quarter': 'Qq yyyy',
        'year': 'y',
    }

    @api.model
    def get_cohort_data(self, date_start, date_stop, measure, interval, domain, mode, timeline):
        """Compute the cohort data required by the cohort view.

        :param str date_start: name of the start date field
        :param str date_stop: name of the stop date field
        :param str measure: field to measure (``__count`` or a field name)
        :param str interval: ``day``, ``week``, ``month``, ``quarter`` or ``year``
        :param list domain: search domain
        :param str mode: ``retention`` or ``churn``
        :param str timeline: ``forward`` or ``backward``
        :returns: dict with ``rows`` and ``avg``
        """
        interval_delta = {
            'day': relativedelta(days=1),
            'week': relativedelta(weeks=1),
            'month': relativedelta(months=1),
            'quarter': relativedelta(months=3),
            'year': relativedelta(years=1),
        }.get(interval, relativedelta(months=1))

        today = date.today()
        display_format = self._cohort_display_formats.get(interval, 'MMMM yyyy')
        period_groupby = '%s:%s' % (date_start, interval)

        groups = self.read_group(domain, ['__count'], [period_groupby], lazy=False)

        columns_avg = {}
        total_value = 0
        total_count = 0
        rows = []

        # read_group on dates is ordered ascending by the start of the period
        for group in groups:
            range_info = (group.get('__range') or {}).get(period_groupby)
            if not range_info:
                # group with an unset date_start: nothing to display
                continue
            cohort_start = self._cohort_period_start(date_start, range_info['from'])

            period_domain = expression.AND([
                [(date_start, '!=', False)],
                [(date_start, '>=', self._cohort_period_bound(date_start, range_info['from']))],
                [(date_start, '<', self._cohort_period_bound(date_start, range_info['to']))],
            ])
            group_domain = expression.AND([domain, period_domain])
            records = self.search(group_domain)

            value = self._cohort_measure(records, measure)
            total_value += value
            total_count += 1

            columns = []
            col_start_date = cohort_start
            if timeline == 'backward':
                col_start_date = cohort_start + self._cohort_shift_period(interval, -15)

            initial_value = value
            initial_churn_value = 0
            for column in range(16):
                if column not in columns_avg:
                    columns_avg[column] = {'percentage': 0, 'count': 0}
                if column != 0:
                    col_start_date = col_start_date + self._cohort_shift_period(interval, 1)
                if col_start_date > today:
                    # future period: no data yet
                    columns.append({'value': '-', 'churn_value': '-', 'percentage': ''})
                    continue

                compare_date = self._cohort_format_period(
                    col_start_date, interval, display_format
                )
                col_records = [
                    record for record in records
                    if record[date_stop]
                    and self._cohort_format_period(
                        fields.Date.to_date(record[date_stop]), interval, display_format
                    ) == compare_date
                ]
                col_value = self._cohort_measure(col_records, measure)

                if timeline == 'backward' and column == 0:
                    col_records = [
                        record for record in records
                        if record[date_stop]
                        and fields.Date.to_date(record[date_stop]) >= col_start_date
                    ]
                    initial_value = self._cohort_measure(col_records, measure)
                    initial_churn_value = value - initial_value

                previous_value = initial_value if column == 0 else columns[column - 1]['value']
                remaining_value = previous_value - col_value
                previous_churn_value = (
                    initial_churn_value if column == 0 else columns[column - 1]['churn_value']
                )
                churn_value = col_value + previous_churn_value

                percentage = remaining_value / value if value else 0
                if mode == 'churn':
                    percentage = 1 - percentage
                percentage = round(100 * percentage, 1)

                columns_avg[column]['percentage'] += percentage
                columns_avg[column]['count'] += 1
                columns.append({
                    'value': remaining_value,
                    'churn_value': churn_value,
                    'percentage': percentage,
                    'domain': [],
                    'period': compare_date,
                })

            rows.append({
                'date': self._cohort_format_period(cohort_start, interval, display_format),
                'value': value,
                'domain': group_domain,
                'columns': columns,
            })

        return {
            'rows': rows,
            'avg': {
                'avg_value': total_value / total_count if total_count else 0,
                'columns_avg': columns_avg,
            },
        }

    def _cohort_measure(self, records, measure):
        if measure == '__count':
            return len(records)
        return sum(records.mapped(measure))

    def _cohort_period_start(self, date_start, range_from):
        """Return the start of the cohort period as a local date.

        For datetime fields ``read_group`` expresses the period bounds in UTC
        (the local period boundaries converted to UTC); convert them back to
        the user's timezone so that column periods are aligned on the actual
        (local) period start.
        """
        if self._fields[date_start].type != 'datetime':
            return fields.Date.from_string(range_from)
        dt = fields.Datetime.from_string(range_from)
        tz = self.env.context.get('tz') or self.env.user.tz or 'UTC'
        local_dt = fields.Datetime.context_timestamp(self.with_context(tz=tz), dt)
        return local_dt.date()

    def _cohort_period_bound(self, date_start, range_bound):
        """Return the period bound in a form suitable for a search domain.

        Date fields expect a date object, datetime fields a datetime/string.
        """
        if self._fields[date_start].type != 'datetime':
            return fields.Date.from_string(range_bound)
        return range_bound

    def _cohort_shift_period(self, interval, amount):
        return {
            'day': relativedelta(days=amount),
            'week': relativedelta(weeks=amount),
            'month': relativedelta(months=amount),
            'quarter': relativedelta(months=3 * amount),
            'year': relativedelta(years=amount),
        }.get(interval, relativedelta(months=amount))

    def _cohort_format_period(self, value, interval, display_format):
        """Format a period date the same way the cohort view does (luxon-like)."""
        if interval == 'week':
            iso = value.isocalendar()
            return 'W%02d %04d' % (iso.week, iso.year)
        if interval == 'quarter':
            return 'Q%d %d' % ((value.month - 1) // 3 + 1, value.year)
        if interval == 'year':
            return str(value.year)
        return format_date(value, format=display_format, locale=get_lang(self.env).code)


class ResPartner(models.Model):
    """Make ``res.partner`` usable in cohort views (demo views)."""

    _name = 'res.partner'
    _inherit = ['res.partner', 'cohort.mixin']
