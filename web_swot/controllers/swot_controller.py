# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import json

from odoo.http import request, Controller, route, Response


class SwotViewController(Controller):

    @route('/web/view/swot/data', type='http', auth='user', methods=['POST'], csrf=False)
    def get_swot_data(self, model=None, q1_domain=None, q2_domain=None, q3_domain=None, q4_domain=None, **kwargs):
        """Hämtar data för SWOT-kvadranterna baserat på domäner."""
        helper = request.env['swot.view.helper']

        # Konvertera domän-strängar till faktiska domäner
        domains = {}
        for i, domain_str in enumerate([q1_domain, q2_domain, q3_domain, q4_domain], 1):
            if domain_str:
                try:
                    domains[f'q{i}'] = eval(domain_str) if isinstance(domain_str, str) else domain_str
                except Exception:
                    domains[f'q{i}'] = []
            else:
                domains[f'q{i}'] = []

        result = helper.get_swot_data(
            model,
            domains['q1'],
            domains['q2'],
            domains['q3'],
            domains['q4'],
        )
        return Response(json.dumps(result), content_type='application/json')
