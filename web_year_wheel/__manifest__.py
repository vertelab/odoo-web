# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Web: Year Wheel View',
    'summary': 'Circular year calendar view showing records on a year wheel',
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
    'auto_install': False,
    'author': 'Vertel AB',
    'license': 'LGPL-3',
}
