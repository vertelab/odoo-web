# Web: Fetch Logo — Configuration

## logo.dev API key (optional)

1. Get a free API key at https://logo.dev (API keys page).
2. In Odoo, go to **Settings → General Settings → Contacts** and set
   **logo.dev API-nyckel**.
3. Save. The key is stored in `ir.config_parameter` under
   `web_fetch_logo.logo_dev_api_key`.

Without a key the chain starts at icon.horse.

## Using the fetcher from your module

### Standalone function (no ORM)

```python
from odoo.addons.web_fetch_logo.models.logo_fetcher import (
    fetch_logo,      # -> bytes | None
    fetch_logo_b64,  # -> str | None  (base64, ready for Binary fields)
)

data = fetch_logo_b64('hetzner.com', api_key='pk_...')  # or None
if data:
    partner.image_1920 = data
```

### Mixin (future use)

```python
class MyModel(models.Model):
    _inherit = ['my.model', 'web.fetch.logo.mixin']

    def fetch_my_logo(self):
        return self.fetch_logo_b64(self.website)  # reads API key from config
```

## Storage

This module does **not** store anything — it only returns content. The
caller stores the logo (e.g. `res.partner.image_1920`). No cache model:
the stored logo is the cache.
