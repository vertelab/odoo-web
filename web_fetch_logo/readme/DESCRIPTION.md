# Web: Fetch Logo

Generic company-logo fetcher for Odoo 18 CE. Exposes a standalone
function and a thin mixin so any module (keykeep, bifrost, ...) can fetch
a company logo from a domain and store it (typically on
`res.partner.image_1920`).

## Tier chain (first success wins)

1. **logo.dev** — vector SVG, used when an API key is configured
   (`web_fetch_logo.logo_dev_api_key`, managed in General Settings near
   Contacts). Requires a free API key from https://logo.dev.
2. **icon.horse** — 192×192 PNG, no key required.
3. **Google favicon service** — 128×128 PNG, reliable fallback.
4. **HTML scraping** (last resort) — parses the site for `og:image`,
   `apple-touch-icon` and `<link rel="icon|logo|shortcut">`.

SVG is preserved when the source delivers it (logo.dev default); scraped
SVG is sanitized against active content (`<script>`, `on*` attributes,
`javascript:` hrefs) before it is returned. Raster formats (PNG/JPEG/WebP)
pass through unchanged.

Fetches never raise: on failure the functions log a warning and return
`None`.
