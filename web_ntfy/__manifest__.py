# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel Sverige AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Web: Ntfy Transport',
    'summary': 'ntfy protocol as a second push transport, under /ntfy/.',
    'description': """Implements the ntfy publish/subscribe protocol inside Odoo,
so notifications get server-side history, priority, tags and action buttons
without running an external ntfy server.

Every user gets a derived, unguessable topic (hmac of database and user id)
reachable at /ntfy/<topic>. Access requires an Odoo session; the topic is an
address, not a credential.

Web push keeps working unchanged. `web.pwa.push._push_user_notification`
fans out to every enabled transport, so callers do not need to know that ntfy
exists.

Known limitation: the iOS ntfy client cannot receive notifications from a
self-hosted server without relaying through ntfy.sh (Apple requires APNs, and
a self-hosted server has no APNs credentials). Use web push on iOS instead.
""",
    'category': 'Hidden',
    'version': '18.0.1.0.0',
    'depends': ['web', 'mail', 'web_pwa_push'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/res_config_settings_views.xml',
    ],
    'author': 'Vertel Sverige AB',
    'website': 'https://vertel.se/apps/odoo-web/web_ntfy',
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}
