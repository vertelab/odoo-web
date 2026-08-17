# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Web: PWA Push',
    'summary': 'PWA installability and web push notifications',
    'description': 'Serves PWA service worker and manifests under /pwa/, per-customer '
                   'branding (inherits web_pwa_customize), VAPID key management, and '
                   'pushes inbox notifications to registered devices.',
    'category': 'Hidden',
    'version': '18.0.1.0.0',
    'depends': ['web_pwa_customize', 'web', 'mail'],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_unit_tests': [
            'web_pwa_push/static/tests/**/*',
        ],
    },
    'author': 'Vertel AB',
    'license': 'LGPL-3',
}
