# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Web: Year Wheel View',
    'summary': 'Circular year calendar view showing records on a year wheel.',
    'description': '''
Year Wheel View
===============

    Circular year calendar view showing records on a year wheel.

    Features:

        - Extends Odoo: Builds on existing Odoo models.
    ''',
    'description': 'Visualizes records on a circular year calendar. '
                   'Useful for seasonal planning, fiscal periods, and yearly overviews.',
    'category': 'Hidden',
    'version': '18.0.1.0.0',
    'depends': ['web'],
    'assets': {
        'web.assets_backend_lazy': [
            'web_year_wheel/static/src/**/*',
        ],
    },
    'demo': [
        'demo/demo_year_wheel_view.xml',
    ],
    'auto_install': False,
    'author': 'Vertel AB',
    'website': 'https://vertel.se/apps/odoo-web/web_year_wheel',
    'license': 'LGPL-3',
}
