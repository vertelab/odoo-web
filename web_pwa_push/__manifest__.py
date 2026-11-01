# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel Sverige AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Web: PWA Push',
    'summary': 'PWA installability and web push notifications.',
    'description': 'Serves PWA service worker and manifests under /pwa/, per-customer '
                   'branding (inherits web_pwa_customize), VAPID key management, and '
                   'pushes inbox notifications to registered devices.',
    'category': 'Hidden',
    'version': '18.0.1.1.1',
    'depends': ['web_pwa_customize', 'web', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/web_pwa_app_data.xml',
        'views/web_pwa_app_views.xml',
        'views/res_config_settings_views.xml',
        'views/webclient_templates.xml',
    ],
    'author': 'Vertel Sverige AB',
    'website': 'https://vertel.se/apps/odoo-web/web_pwa_push',
    'license': 'LGPL-3',
}
