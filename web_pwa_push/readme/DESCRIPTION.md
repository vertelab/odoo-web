# Web PWA Push

Serves PWA service worker and manifests under `/pwa/`, per-customer branding
(inherits `web_pwa_customize`), VAPID key management, and pushes inbox
notifications to registered devices.

- `/pwa/sw.js` — pass-through service worker with push listener
  (`Service-Worker-Allowed: /ai/`)
- `/pwa/manifest/ai-chat` — installable manifest for the AI chat
- `/pwa/vapid-public-key` — public VAPID key for device registration
- `/pwa/install` — generic install hub
- `/web/manifest.webmanifest` — customer-branded backend manifest
  (inherits OCA `web_pwa_customize`)
