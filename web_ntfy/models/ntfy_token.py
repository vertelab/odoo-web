# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel Sverige AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import hashlib
import logging
import secrets

from odoo import api, fields, models
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)

TOKEN_TTL_HOURS = 24


class NtfyToken(models.Model):
    """Short-lived Bearer token for clients that cannot hold a session.

    A browser keeps an Odoo session cookie; a cron job piping into `curl`
    cannot. Those exchange an Odoo API key for a token at /ntfy/auth.

    The token is stored hashed — reading the table must not yield a usable
    credential. In production the exchange should hand the secret to keykeep
    rather than a Char field; this table only holds the hash and the mapping.
    """

    _name = 'ntfy.token'
    _description = 'Ntfy Bearer Token'
    _order = 'create_date desc'

    user_id = fields.Many2one('res.users', string='User', required=True,
                              ondelete='cascade', index=True, readonly=True)
    token_hash = fields.Char(string='Token Hash', required=True, index=True,
                             readonly=True)
    expires_at = fields.Datetime(string='Expires At', required=True, readonly=True)
    last_used = fields.Datetime(string='Last Used', readonly=True)

    @api.model
    def _hash(self, raw):
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    @api.model
    def _issue(self, user):
        """Mint a token for a user and return the raw value (shown once)."""
        raw = secrets.token_urlsafe(32)
        self.sudo().create({
            'user_id': user.id,
            'token_hash': self._hash(raw),
            'expires_at': fields.Datetime.add(fields.Datetime.now(), hours=TOKEN_TTL_HOURS),
        })
        return raw

    @api.model
    def _authenticate(self, raw):
        """Resolve a raw token to a user, or raise AccessDenied."""
        if not raw:
            raise AccessDenied('Missing token')
        token = self.sudo().search([('token_hash', '=', self._hash(raw))], limit=1)
        if not token:
            raise AccessDenied('Invalid token')
        if token.expires_at and token.expires_at < fields.Datetime.now():
            token.sudo().unlink()
            raise AccessDenied('Token expired')
        token.sudo().write({'last_used': fields.Datetime.now()})
        return token.user_id
