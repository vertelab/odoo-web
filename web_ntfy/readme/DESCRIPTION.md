# Web Ntfy Transport

Implements the [ntfy](https://ntfy.sh) publish/subscribe protocol inside
Odoo, under `/ntfy/` on the customer's own domain. Notifications get
server-side history, priority, tags and action buttons — without running an
external ntfy server.

## Why not the ntfy Go server

The ntfy server's publish API is a URL path, some headers, a JSON body and a
stream. That is a few hundred lines of Python. What the Go server adds beyond
that — attachments, e-mail, UnifiedPush, a web UI — we do not need, because
Odoo is the UI.

## URLs

| Method | Path | Purpose |
|---|---|---|
| `POST`/`PUT` | `/ntfy/<topic>` | Publish a message |
| `GET` | `/ntfy/<topic>/json` | JSON stream (or poll with `?poll=1`) |
| `GET` | `/ntfy/<topic>/sse` | Same stream as Server-Sent Events |
| `POST` | `/ntfy/auth` | Exchange an Odoo API key for a Bearer token |

## The topic is an address, not a credential

Each user's topic is derived, never stored:

```
topic = hmac_sha256(salt, "{database}:{user_id}")[:32]
```

The salt lives in `ir.config_parameter` (`web_ntfy.salt`) and is generated on
first use. Rotating it re-addresses every user at once.

The topic is unguessable (256 bits of HMAC output), but it grants nothing on
its own: every request still needs an Odoo session or a Bearer token. That is
why no field on `res.users` holds a secret.

## Authentication

**Browsers** use the normal Odoo session cookie.

**Cron jobs and scripts** exchange an Odoo API key for a token:

```bash
TOKEN=$(curl -s -X POST https://customer.se/ntfy/auth \
  -H 'Content-Type: application/json' \
  -d '{"login":"user@example.com","api_key":"..."}' | jq -r .token)

curl -H "Authorization: Bearer $TOKEN" \
     -d "Backup finished" https://customer.se/ntfy/<topic>
```

Tokens live 24 hours and are stored hashed in `ntfy.token`. In production the
exchange should hand the secret to keykeep rather than a Char field; this
table only holds the hash.

## Settings

All settings are **server decisions**, in `res.config.settings` — not per-user.
A user cannot know whether the server has ntfy turned on.

| Setting | Default | Meaning |
|---|---|---|
| `ntfy_enabled` | off | Serve `/ntfy/` and deliver through it |
| `ntfy_transport_web_push` | on | Keep delivering via web push |
| `ntfy_transport_ntfy` | on | Also deliver via the ntfy topic |
| `ntfy_retention_days` | 7 | Daily cron deletes older messages |
| `ntfy_max_priority` | max | Cap on requested priority |

## Fan-out

`web.pwa.push._push_user_notification()` delivers to every enabled transport.
Callers do not need to change:

```python
env['web.pwa.push']._push_user_notification(
    user, title='Done', body='The coworker replied.', url='/ai/chat')
```

The signature gained an optional `transports` argument, so existing calls
(`ai_agent_core`'s done-notification and HITL prompts) keep working unchanged.

## Known limitations

**iOS cannot use this without a relay.** The protocol is identical to
Android's, but iOS only allows waking a device through APNs, and a
self-hosted server has no APNs credentials. The ntfy iOS app therefore
requires the server to forward a `poll_request` to `ntfy.sh` — which means
the existence, timestamp and `sha256(topic URL)` of every notification leave
our infrastructure. For a hosting provider that is a privacy decision, not an
implementation detail. **Use web push on iOS instead** — it works from iOS
16.4 and needs no relay.

**Subpath hosting.** Upstream says ntfy needs a subdomain, but that constraint
exists because the ntfy web UI emits absolute `/static/` paths. We serve no web
UI, so it does not apply. Clients verified against `/ntfy/`:

| Client | Subpath |
|---|---|
| `curl` / CLI | works |
| Browser | works |
| ntfy-android | partial (upstream #1026) |
| Ntfyr (GNOME) | inherits the same client code |
| ntfy-ios | not applicable — see above |

## Retention

`ntfy.message` grows. A daily cron deletes messages older than
`ntfy_retention_days`, but **never undelivered ones** — deleting those would
mean the recipient never had a chance to read them, which is exactly the loss
web push already suffers from.

## License

LGPL-3.0 or later. Copyright (C) 2026 Vertel Sverige AB.
