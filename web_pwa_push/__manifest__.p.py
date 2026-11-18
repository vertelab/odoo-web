# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Web: PWA Push',
    'summary': 'PWA installability and web push notifications.',
    'description': '''
PWA Push
========

    PWA installability and web push notifications.

    Features:

        - Web integration: Exposes HTTP endpoints for external systems.
        - UI Integration: Extends 2 view(s) in the Odoo interface.
        - Extends Odoo: Builds on mail.notification, web.pwa.push.
    ''',
    'description': 'Serves PWA service worker and manifests under /pwa/, per-customer '
                   'branding (inherits web_pwa_customize), VAPID key management, and '
                   'pushes inbox notifications to registered devices.',
    'category': 'Hidden',
    'version': '1.0.0',
    # #if VERSION <= "19.0"
    'depends': ['web_pwa_customize', 'web', 'mail'],
    # #else
    # DOCUMENTED FUNCTION LOSS in 20.0: web_pwa_customize is not ported in
    # OCA/web, so the dependency is dropped. The controller already handles it —
    # the import is in try/except and the WebManifest override is defined only
    # when the import succeeds. Consequence: the customer-branded backend
    # webmanifest is not applied in 20.0; push notifications and the service
    # worker are unaffected.
    'depends': ['web', 'mail'],
    # #endif
    'data': [
        'views/res_config_settings_views.xml',
        'views/webclient_templates.xml',
    ],
    'author': 'Vertel AB',
    'website': 'https://vertel.se/apps/odoo-web/web_pwa_push',
    'license': 'LGPL-3',
}
