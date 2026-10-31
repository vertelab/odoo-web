# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel Sverige AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import base64

from odoo import fields, models
from odoo.tools import file_open


class ResCompany(models.Model):
    _inherit = 'res.company'

    # ── PWA (mobilapp) branding ──
    pwa_icon = fields.Image(
        'PWA-ikon',
        help='Ikon på hemskärmen för den installerade appen. Lämnas tom '
             'används företagsloggan, därefter modulikonen.')

    def pwa_app_name(self, app='chat'):
        """Resolve the PWA app name per branding chain.

        Konfigurerat (ir.config_parameter web_pwa_push.pwa_app_name) →
        registrerad web.pwa.app (dess name) → default per app:
        'AI <företagsnamn>' för chatten, företagsnamnet för backend
        (respekterar web.web_app_name om det satts explicit).

        Registret konsulteras före de hårdkodade fallen så en ny app får sitt
        namn utan att den här metoden ändras. 'chat' och 'backend' behåller
        sina defaults när ingen app-post finns, så /ai/chat och /odoo beter sig
        exakt som förut.
        """
        self.ensure_one()
        icp = self.env['ir.config_parameter'].sudo()
        configured = (icp.get_param('web_pwa_push.pwa_app_name', '') or '').strip()
        if configured:
            return configured
        # Registrerade appar äger sitt namn.
        if 'web.pwa.app' in self.env:
            registered = self.env['web.pwa.app'].sudo()._get_app(app)
            if registered and registered.name:
                return registered.name
        if app == 'backend':
            if icp.search_count([('key', '=', 'web.web_app_name')]):
                return icp.get_param('web.web_app_name', 'Odoo')
            return self.name or 'Odoo'
        return ('AI ' + (self.name or '')).strip() or 'AI Chat'

    def pwa_icon_bytes(self):
        """Return the PWA icon source as raw bytes (PNG).

        Upplösningskedja: konfigurerad ikon → res.company.logo → icon.png.
        Returnerar None om ingen källa finns.
        """
        self.ensure_one()
        for src in (self.pwa_icon, self.logo):
            if src:
                try:
                    return base64.b64decode(src)
                except Exception:
                    continue
        try:
            with file_open('web_pwa_push/static/description/icon.png', 'rb') as f:
                return f.read()
        except Exception:
            return None
