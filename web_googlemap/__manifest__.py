# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel Sverige AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Web: Google Map View',
    'summary': 'Google Maps view type for the Odoo backend.',
    'description': '''
Web: Google Map View
====================

    A ``googlemap`` view type for the Odoo backend, backed by the Google
    Maps JavaScript API.

    The view is generic: it renders any model that has a ``partner_id``
    field, or a model whose records carry ``latitude``/``longitude``.
    Domain-specific map views (work orders, equipment, key positions) are
    built on top of it in the modules that own those models.

    Features:

        - ``googlemap`` view type, selectable in ``ir.ui.view`` and
          ``ir.actions.act_window.view``
        - API key entered once in Settings and read by the frontend
        - Default view builder for models with a contact field
    ''',
    'version': '18.0.1.0.0',
    'author': 'Vertel Sverige AB',
    'website': 'https://vertel.se/apps/odoo-web/web_googlemap',
    'license': 'LGPL-3',
    'category': 'Hidden',
    'depends': [
        'base_setup',
        'base',
        'web',
        'contacts',
    ],
    'data': [
        'views/res_config_settings.xml',
        'views/contact_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'web_googlemap/static/src/googlemap_view/googlemap_view.js',
            'web_googlemap/static/src/googlemap_view/googlemap_controller.js',
            'web_googlemap/static/src/googlemap_view/googlemap_renderer.js',
            'web_googlemap/static/src/googlemap_view/googlemap_model.js',
            'web_googlemap/static/src/googlemap_view/googlemap_arch_parser.js',
            'web_googlemap/static/src/googlemap_view/googlemap_controller.scss',
            'web_googlemap/static/src/googlemap_view/googlemap_renderer.scss',
            'web_googlemap/static/src/googlemap_view/googlemap.scss',
            'web_googlemap/static/src/googlemap_view/googlemap_controller.xml',
            'web_googlemap/static/src/googlemap_view/googlemap_renderer.xml',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
