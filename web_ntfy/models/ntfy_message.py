# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel Sverige AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import logging
import time
import uuid

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

PRIORITIES = [
    ('min', 'Min'),
    ('low', 'Low'),
    ('default', 'Default'),
    ('high', 'High'),
    ('max', 'Max'),
]
PRIORITY_RANK = {'min': 1, 'low': 2, 'default': 3, 'high': 4, 'max': 5}


class NtfyMessage(models.Model):
    """A published ntfy message.

    This is the history web push does not have: a delivered-or-not record of
    every notification, queryable by `since=` the way ntfy clients expect.

    Rows carry the topic they were published to. The topic is derived from the
    user, so the row can be attributed back to a user without storing any
    secret — see ntfy.topic.
    """

    _name = 'ntfy.message'
    _description = 'Ntfy Message'
    _order = 'create_date desc, id desc'
    _rec_name = 'message_id'

    topic = fields.Char(
        string='Topic', required=True, index=True, readonly=True,
        help='Derived per-user topic. Not a secret — an address.')
    message_id = fields.Char(
        string='Message ID', required=True, readonly=True, default=lambda s: s._ntfy_id(),
        help='ntfy message id, 12 characters, used by since=/poll=1.')
    title = fields.Char(string='Title', readonly=True)
    body = fields.Text(string='Body', readonly=True)
    priority = fields.Selection(PRIORITIES, string='Priority', default='default', readonly=True)
    tags = fields.Char(
        string='Tags', readonly=True,
        help='Comma-separated ntfy tags (emoji shortcodes), e.g. "warning,skull".')
    click = fields.Char(
        string='Click URL', readonly=True,
        help='URL opened when the notification is tapped.')
    actions = fields.Text(
        string='Actions', readonly=True,
        help='ntfy action specification (view/http/broadcast), one per line.')
    event = fields.Char(
        string='Event', default='message', readonly=True,
        help='ntfy event type: message, keepalive, open, poll_request.')
    user_id = fields.Many2one(
        'res.users', string='Recipient', readonly=True, index=True,
        help='Owner of the topic. Used for access control on the stream.')
    delivered = fields.Boolean(
        string='Delivered', readonly=True,
        help='Set when a subscriber has read the message; protects it from retention.')

    _sql_constraints = [
        ('message_id_uniq', 'unique(message_id)', 'Message id must be unique.'),
    ]

    @api.model
    def _ntfy_id(self):
        """ntfy ids are 12 alphanumeric characters."""
        return uuid.uuid4().hex[:12]

    def init(self):
        """Index the query the stream actually runs: topic + recency."""
        self.env.cr.execute(
            'CREATE INDEX IF NOT EXISTS ntfy_message_topic_create_date_idx '
            'ON ntfy_message (topic, create_date DESC)'
        )
        self.env.cr.execute(
            'CREATE INDEX IF NOT EXISTS ntfy_message_user_id_idx '
            'ON ntfy_message (user_id)'
        )

    def _to_ntfy_json(self):
        """Serialise one message the way ntfy clients expect.

        The field set follows the ntfy publish/subscribe JSON contract; extra
        keys would be ignored by clients but this keeps the payload small.
        """
        self.ensure_one()
        data = {
            'id': self.message_id,
            'time': int(self.create_date.timestamp()) if self.create_date else int(time.time()),
            'event': self.event or 'message',
            'topic': self.topic,
        }
        if self.title:
            data['title'] = self.title
        if self.body:
            data['message'] = self.body
        if self.priority and self.priority != 'default':
            data['priority'] = PRIORITY_RANK.get(self.priority, 3)
        if self.tags:
            data['tags'] = [t.strip() for t in self.tags.split(',') if t.strip()]
        if self.click:
            data['click'] = self.click
        if self.actions:
            data['actions'] = [
                dict(pair.split('=', 1) for pair in line.split(',') if '=' in pair)
                for line in self.actions.splitlines() if line.strip()
            ]
        return data

    @api.model
    def _publish(self, user, title=None, body=None, priority=None, tags=None,
                 click=None, actions=None):
        """Create a message on the user's topic."""
        topic_model = self.env['ntfy.topic']
        topic = topic_model._topic_for_user(user)
        if not topic:
            return self.browse()
        max_priority = self.env['ir.config_parameter'].sudo().get_param(
            'web_ntfy.max_priority', 'max')
        if priority and PRIORITY_RANK.get(priority, 3) > PRIORITY_RANK.get(max_priority, 5):
            priority = max_priority
        return self.sudo().create({
            'topic': topic,
            'title': title,
            'body': body,
            'priority': priority or 'default',
            'tags': tags,
            'click': click,
            'actions': actions,
            'user_id': user.id if user else False,
        })

    @api.model
    def _since(self, topic, since=None):
        """Return messages on a topic, oldest first, for the stream/poll API.

        `since` follows the ntfy contract: 'all', a message id, a unix
        timestamp, or empty (meaning "from now on").
        """
        domain = [('topic', '=', topic)]
        if since == 'all':
            pass
        elif since and since.isdigit():
            domain += [('create_date', '>', fields.Datetime.from_timestamp(int(since)))]
        elif since:
            prior = self.sudo().search([('topic', '=', topic), ('message_id', '=', since)], limit=1)
            if prior:
                domain += [('id', '>', prior.id)]
        else:
            return self.browse()
        return self.sudo().search(domain, order='id asc')

    @api.model
    def _cron_retention(self):
        """Delete messages past the retention window (daily cron).

        A history nobody prunes becomes a burden, so this runs from day one.
        Undelivered messages are exempt: deleting one would mean the recipient
        never had a chance to read it, which is precisely the loss web push
        already suffers from.
        """
        icp = self.env['ir.config_parameter'].sudo()
        try:
            days = int(icp.get_param('web_ntfy.retention_days', '7'))
        except (TypeError, ValueError):
            days = 7
        if days <= 0:
            _logger.info('web_ntfy: retention disabled (days=%s)', days)
            return 0
        cutoff = fields.Datetime.subtract(fields.Datetime.now(), days=days)
        stale = self.sudo().search([
            ('create_date', '<', cutoff),
            ('delivered', '=', True),
        ])
        count = len(stale)
        if count:
            stale.unlink()
            _logger.info('web_ntfy: deleted %s messages older than %s days', count, days)
        return count
