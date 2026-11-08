# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel Sverige AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import hashlib
import hmac
import logging
import secrets

from odoo import api, models

_logger = logging.getLogger(__name__)

SALT_PARAM = 'web_ntfy.salt'
TOPIC_LENGTH = 32


class NtfyTopic(models.AbstractModel):
    """Derives a user's ntfy topic.

    The topic is an ADDRESS, not a credential: it is unguessable (256 bits of
    HMAC output) but grants nothing on its own — every request still needs an
    Odoo session or a Bearer token. That is why it is derived rather than
    stored: no field on res.users holds a secret, and rotating the salt
    re-addresses every user at once.

    Format: hmac_sha256(salt, "{db}:{user_id}")[:32] as lowercase hex.
    """

    _name = 'ntfy.topic'
    _description = 'Ntfy Topic Derivation'

    @api.model
    def _get_salt(self):
        """Return the HMAC salt, creating it on first use."""
        icp = self.env['ir.config_parameter'].sudo()
        salt = icp.get_param(SALT_PARAM)
        if not salt:
            salt = secrets.token_hex(32)
            icp.set_param(SALT_PARAM, salt)
            _logger.info('web_ntfy: generated topic salt')
        return salt

    @api.model
    def _topic_for_user(self, user):
        """Return the user's topic string, or False if the user is unusable."""
        if not user:
            return False
        user = user.sudo()
        if not user.id:
            return False
        message = '%s:%s' % (self.env.cr.dbname, user.id)
        digest = hmac.new(
            self._get_salt().encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()
        return digest[:TOPIC_LENGTH]

    @api.model
    def _user_for_topic(self, topic):
        """Resolve a topic back to its user, or an empty recordset.

        Topics are derived per user, so a lookup has to test candidates. The
        user base is small enough for this to be cheap, and the alternative —
        storing the topic — is exactly what we are avoiding.
        """
        if not topic:
            return self.env['res.users']
        users = self.env['res.users'].sudo().search([('active', 'in', [True, False])])
        for user in users:
            if hmac.compare_digest(self._topic_for_user(user), topic):
                return user
        return self.env['res.users']

    @api.model
    def _is_enabled(self):
        icp = self.env['ir.config_parameter'].sudo()
        return icp.get_param('web_ntfy.enabled', 'False') == 'True'
