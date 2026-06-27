# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import http
from odoo.http import request


class CohortController(http.Controller):

    @http.route('/web_cohort_ce/static/src/cohort_view_sample_server.js', type='http', auth='user')
    def cohort_sample_data(self, **kwargs):
        return request.render('web_cohort_ce.cohort_sample_data', {})
