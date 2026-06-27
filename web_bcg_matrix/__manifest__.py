# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Web: BCG Matrix View',
    'summary': 'Boston Consulting Group matrix view (4-quadrant scatter plot)',
    'description': 'Visualizes records in a 2x2 matrix based on two numeric fields. '
                   'Useful for portfolio analysis, risk assessment, and customer segmentation.',
    'category': 'Hidden',
    'version': '18.0.1.0.0',
    'depends': ['web'],
    'assets': {
        'web.assets_backend_lazy': [
            'web_bcg_matrix/static/src/**/*',
        ],
    },
    'auto_install': False,
    'author': 'Vertel AB',
    'license': 'LGPL-3',
}
