# Configuration

Settings → General Settings → Progressive Web App:

1. **App-namn** — the installed app name. Empty = "AI <company name>" for
   the chat, company name for the backend.
2. **Icon** — upload an icon (SVG or PNG ≥ 512×512). Empty = company logo
   (auto-converted to PNG), then the module icon.
3. **Colors** — background/theme color (inherited from `web_pwa_customize`).
4. **Web Push (VAPID-keys)** — click "Generera nyckelpar" to create the
   keypair. Keys are stored in `ir.config_parameter` under
   `mail.web_push_vapid_*` (same parameters Odoo's native web push reads).
   Rotation invalidates all subscriptions — generate once.

VAPID keys can also be set via pillar/Salt → `ir.config_parameter`.
`base_url` must be correct for push delivery.
