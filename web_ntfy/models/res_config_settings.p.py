# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel Sverige AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models

TRANSPORTS = ('web_push', 'ntfy')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ntfy_enabled = fields.Boolean(
        string='Enable ntfy transport',
        config_parameter='web_ntfy.enabled',
        help='Serve the ntfy protocol under /ntfy/ and deliver notifications '
             'through it. This is a server decision: an individual user cannot '
             'know whether the server has ntfy turned on.')
    ntfy_transport_web_push = fields.Boolean(
        string='Deliver via web push',
        config_parameter='web_ntfy.transport_web_push',
        default=True,
        help='Keep delivering through Odoo web push (mail.push.device).')
    ntfy_transport_ntfy = fields.Boolean(
        string='Deliver via ntfy',
        config_parameter='web_ntfy.transport_ntfy',
        default=True,
        help='Also deliver through the ntfy topic.')
    ntfy_retention_days = fields.Integer(
        string='Keep ntfy messages (days)',
        config_parameter='web_ntfy.retention_days',
        default=7,
        help='Messages older than this are deleted by the daily cron. '
             'Undelivered messages are never deleted.')
    ntfy_max_priority = fields.Selection(
        [('min', 'Min'), ('low', 'Low'), ('default', 'Default'),
         ('high', 'High'), ('max', 'Max')],
        string='Highest allowed priority',
        config_parameter='web_ntfy.max_priority',
        default='default',
        help='Messages asking for a higher priority are capped to this.')
