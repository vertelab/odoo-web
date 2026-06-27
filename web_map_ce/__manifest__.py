# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Web: Map View CE',
    'summary': 'Map view for Odoo Community Edition (OpenStreetMap-based)',
    'description': 'Allows viewing records on a map using Leaflet and OpenStreetMap/Nominatim.',
    'category': 'Hidden',
    'version': '18.0.1.0.0',
    'depends': ['web', 'base_setup'],
    'data': [
        # 'views/res_config_settings.xml',  # TODO: uncomment when base partner form is stable
        # 'views/res_partner_views.xml',  # TODO: uncomment when base partner form is stable
    ],
    'demo': [
        'demo/demo_map_view.xml',
    ],
    'auto_install': True,
    'author': 'Vertel AB',
    'license': 'LGPL-3',
    'assets': {
        'web.assets_backend_lazy': [
            'web_map_ce/static/src/**/*',
        ],
        'web.assets_unit_tests': [
            'web_map_ce/static/lib/**/*',
            'web_map_ce/static/tests/**/*',
        ],
        'web.qunit_suite_tests': [
            'web_map_ce/static/lib/**/*',
        ],
    },
}
