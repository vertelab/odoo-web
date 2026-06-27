# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Web: Gantt View CE',
    'summary': 'Gantt chart view for Odoo Community Edition',
    'description': 'Provides a Gantt chart view for project planning and scheduling.',
    'category': 'Hidden',
    'version': '18.0.1.0.0',
    'depends': ['web'],
    'assets': {
        'web.assets_backend_lazy': [
            'web_gantt_ce/static/src/**/*',
        ],
        'web.assets_unit_tests': [
            'web_gantt_ce/static/tests/**/*',
        ],
    },
    'demo': [
        'demo/demo_gantt_view.xml',
    ],
    'auto_install': True,
    'author': 'Vertel AB',
    'license': 'LGPL-3',
}
