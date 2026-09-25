{
    'name': 'Web: Generic SWOT View',
    'version': '18.0.1.0.0',
    'category': 'Tools',
    'summary': "Adds SWOT analysis views.",
    'description': '''
Generic SWOT View
=================

    This module adds a new generic view type for SWOT analysis that can be used
with any Odoo model. Each quadrant can be configured with its own domain to
filter and categorise data.

Features:

    - Generic SWOT view type that works with all models.
    - Configurable domain per quadrant.
    - Visual 2x2 matrix layout.
    - Clickable records that open the detail view.
    - Responsive design.
    - Customisable titles per quadrant.
    ''',
    'author': 'Ditt företag',
    'website': 'https://vertel.se/apps/odoo-web/web_swot',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'web'
    ],
    'data': [
        #### 2025-11-12 'views/example_views.xml',  # Exempel på användning
    ],
    'demo': [
        'demo/demo_swot_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'web_swot/static/src/**/*',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,  # Detta är en utility-modul, inte en app
}
