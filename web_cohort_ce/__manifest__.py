# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Web: Cohort View CE',
    'summary': 'Cohort view for Odoo Community Edition',
    'category': 'Hidden',
    'version': '18.0.1.0.0',
    'depends': ['web'],
    'assets': {
        'web.assets_backend_lazy': [
            'web_cohort_ce/static/src/**/*',
        ],
        'web.assets_unit_tests': [
            'web_cohort_ce/static/tests/**/*.js',
        ],
    },
    'demo': [
        'demo/demo_cohort_view.xml',
    ],
    'auto_install': True,
    'author': 'Vertel AB',
    'license': 'LGPL-3',
}
