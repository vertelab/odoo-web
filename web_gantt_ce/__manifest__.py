# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel Sverige AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Web: Gantt View CE',
    'summary': 'Gantt chart view for Odoo Community Edition.',
    'description': '''
Gantt View CE
=============

    Gantt chart view for Odoo Community Edition.

    Features:

        - Extends Odoo: Builds on gantt.mixin.
    ''',
    'description': 'Provides a Gantt chart view for project planning and scheduling.',
    'category': 'Hidden',
    'version': '18.0.1.0.9',
    'depends': ['web'],
    'assets': {
        # SCSS variables must be compiled before the stylesheets that use
        # them. A bare ``static/src/**/*`` glob sorts alphabetically, which
        # puts ``gantt_view.scss`` before ``gantt_view.variables.scss`` and
        # breaks the whole lazy bundle with:
        #   Undefined variable: "$gantt-highlight-today-bg"
        # Odoo core solves this by collecting every ``*.variables.scss`` into
        # ``web._assets_primary_variables``, which ``web._assets_helpers``
        # includes first in every bundle. Mirror that here.
        'web._assets_primary_variables': [
            'web_gantt_ce/static/src/**/*.variables.scss',
        ],
        'web.assets_backend_lazy': [
            'web_gantt_ce/static/src/**/*',

            # Don't include dark mode files in light mode
            ('remove', 'web_gantt_ce/static/src/**/*.dark.scss'),
        ],
        'web.assets_backend_lazy_dark': [
            'web_gantt_ce/static/src/**/*.dark.scss',
        ],
        'web.assets_unit_tests': [
            'web_gantt_ce/static/tests/**/*',
        ],
    },
    'demo': [
        'demo/demo_gantt_view.xml',
    ],
    'auto_install': True,
    'author': 'Vertel Sverige AB',
    'website': 'https://vertel.se/apps/odoo-web/web_gantt_ce',
    'license': 'LGPL-3',
}
