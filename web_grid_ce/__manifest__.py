# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Web: Grid View CE',
    'summary': 'Editable 2D grid view for Odoo Community Edition',
    'description': 'Provides a read/write 2D grid view for pivoting data.',
    'category': 'Hidden',
    'version': '18.0.1.0.0',
    'depends': ['web'],
    'assets': {
        'web.assets_backend_lazy': [
            'web_grid_ce/static/src/**/*',
        ],
        'web.assets_unit_tests': [
            'web_grid_ce/static/tests/**/*.test.js',
        ],
    },
    'auto_install': True,
    'author': 'Vertel AB',
    'license': 'LGPL-3',
}
