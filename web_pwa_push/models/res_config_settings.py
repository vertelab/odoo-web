# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import base64
import logging

from odoo import fields, models
from odoo.addons.mail.tools.jwt import generate_vapid_keys
from odoo.tools import image_process

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    """Ärver web_pwa_customize:s settings (short_name, färger, ikon) och
    utökar med: app-namn, VAPID-nycklar (generera-knapp).

    Ikon-URL-basen överrids till vårt eget namespace (/web_pwa_push/icon)
    — OCA:s metoder (get_values/set_values/_write_icon_to_attachment)
    använder self._pwa_icon_url_base, så arvet följer med.
    """
    _inherit = 'res.config.settings'
    _pwa_icon_url_base = '/web_pwa_push/icon'

    pwa_app_name = fields.Char(
        'App-namn',
        config_parameter='web_pwa_push.pwa_app_name',
        help='Namn på den installerade appen. Tomt = "AI <företagsnamn>" för '
             'chatten, företagsnamnet för backend.')

    pwa_icon = fields.Image(
        related='company_id.pwa_icon', string='PWA-ikon', readonly=False,
        help='Ikon på hemskärmen. Tomt = företagsloggan, därefter modulikonen.')

    pwa_vapid_private_key = fields.Char(
        'VAPID privat nyckel',
        config_parameter='mail.web_push_vapid_private_key',
        help='Web Push VAPID privat nyckel (hemlig). Generera en gång — '
             'rotera bara vid kompromiss (alla enheter måste prenumerera om).')

    pwa_vapid_public_key = fields.Char(
        'VAPID publik nyckel',
        config_parameter='mail.web_push_vapid_public_key',
        help='Web Push VAPID publik nyckel. Skickas till webbläsarna vid '
             'prenumeration.')

    def generate_vapid_keys(self):
        """Generate a fresh VAPID keypair into the settings fields.

        Anropas från settings-vyns knapp. Fälten sparas till
        ir.config_parameter via config_parameter-mekanismen när settings
        sparas (set_values).
        """
        private_key_value, public_key_value = generate_vapid_keys()
        self.pwa_vapid_private_key = private_key_value
        self.pwa_vapid_public_key = public_key_value
        return {
            'type': 'ir.actions.act_window_close',
        }

    def set_values(self):
        """Utökar OCA:s set_values med:
        - logo-fallback: ingen uppladdad ikon men företagslogga finns →
          normalisera till PNG (512×512) och använd som ikonkälla (hosting-
          kunden slipper ladda upp).
        - apple-touch-ikon 180×180 (iOS kräver den för hemskärmen; OCA
          genererar bara 128–512).
        """
        if not self.pwa_icon and self.company_id.logo:
            try:
                logo_bytes = base64.b64decode(self.company_id.logo)
                png = image_process(
                    logo_bytes, size=(512, 512), expand=True,
                    colorize=(255, 255, 255), padding=0)
                self.pwa_icon = base64.b64encode(png)
            except Exception:
                _logger.warning('web_pwa_push: logo fallback failed', exc_info=True)
        res = super().set_values()
        if self.pwa_icon:
            try:
                self._write_icon_to_attachment('.png', 'image/png', size=(180, 180))
            except Exception:
                _logger.warning(
                    'web_pwa_push: apple-touch icon (180) generation failed',
                    exc_info=True)
        return res
