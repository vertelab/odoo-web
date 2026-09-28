# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

"""Generic company-logo fetcher (no ORM dependency).

Standalone module-level functions:
    fetch_logo(domain, api_key=None, ...)     -> bytes | None
    fetch_logo_b64(domain, api_key=None, ...) -> str | None

Tier chain (first success wins):
    1. logo.dev      -- SVG, requires an API key (pk_...)
    2. icon.horse    -- PNG, no key
    3. Google        -- PNG favicon service
    4. HTML scraping -- og:image / apple-touch-icon / link rel=icon
                        (last resort; scraped SVG is sanitized)

The functions never raise on fetch failures -- they log a warning and
return ``None`` so callers can decide how to surface the outcome.
"""

import base64
import logging
import re
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree

import requests

_logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 15
DEFAULT_MAX_BYTES = 5_000_000
SCRAPE_HTML_LIMIT = 500_000
USER_AGENT = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
              '(KHTML, like Gecko) Chrome/120 Safari/537.36 '
              'Odoo-WebFetchLogo/1.0')

_LOGO_DEV_URL = 'https://img.logo.dev/{domain}'
_ICON_HORSE_URL = 'https://icon.horse/icon/{domain}'
_GOOGLE_FAVICON_URL = 'https://www.google.com/s2/favicons'

_SVG_NS = 'http://www.w3.org/2000/svg'

# Elements/attributes that can carry active content in SVG.
_SVG_ACTIVE_ELEMENTS = ('script', 'foreignObject', 'foreignobject')
_SVG_ACTIVE_ATTR_PREFIXES = ('on',)
_SVG_ACTIVE_ATTR_NAMES = ('href',)


def _localname(tag):
    """Strip the XML namespace from an ElementTree tag/attribute name."""
    return tag.rsplit('}', 1)[-1] if '}' in tag else tag


def extract_domain(value):
    """Extract a bare domain from a URL or a domain string.

    ``'https://www.hetzner.com/pricing'`` -> ``'hetzner.com'``
    ``'hetzner.com'``                     -> ``'hetzner.com'``

    Returns ``''`` for empty or invalid input.
    """
    if not value:
        return ''
    value = str(value).strip()
    if not value:
        return ''
    if '://' not in value:
        value = '//' + value
    try:
        parsed = urlparse(value)
        host = parsed.netloc or parsed.path
    except ValueError:
        return ''
    # strip userinfo, port; lowercase; strip common www. prefix
    host = host.split('@')[-1].split(':')[0].strip().lower()
    if host.startswith('www.'):
        host = host[4:]
    if not host or '.' not in host or ' ' in host:
        return ''
    return host


def sanitize_svg_xml(data):
    """Return sanitized SVG bytes, or ``None`` if the SVG is unparsable.

    Removes active content that could carry scripted behavior:
    ``<script>``/``<foreignObject>`` elements, ``on*`` attributes and
    ``javascript:`` hrefs. Raster images are never passed here.

    Rejects (returns ``None``) on parse failure rather than returning a
    possibly-unsafe blob.
    """
    if not data:
        return None
    try:
        # Keep the default SVG namespace on re-serialization (deterministic
        # output instead of auto-generated ``ns0:`` prefixes).
        ElementTree.register_namespace('', _SVG_NS)
        root = ElementTree.fromstring(data)
    except ElementTree.ParseError:
        return None

    def _sanitize_node(el):
        if _localname(el.tag) in _SVG_ACTIVE_ELEMENTS:
            return False  # drop this subtree
        for child in list(el):
            if not _sanitize_node(child):
                el.remove(child)
        for attr in list(el.attrib):
            local = _localname(attr)
            value = str(el.attrib[attr]).strip().lower()
            if local.startswith(_SVG_ACTIVE_ATTR_PREFIXES) or (
                local in _SVG_ACTIVE_ATTR_NAMES
                and value.startswith('javascript:')
            ):
                del el.attrib[attr]
        return True

    if not _sanitize_node(root):
        return None
    return ElementTree.tostring(root)


class LogoFetcher:
    """Fetches a company logo for a domain through a tier chain."""

    def __init__(self, api_key=None, timeout=DEFAULT_TIMEOUT,
                 max_bytes=DEFAULT_MAX_BYTES):
        self.api_key = api_key or ''
        self.timeout = timeout
        self.max_bytes = max_bytes

    # -- public -------------------------------------------------------

    def fetch(self, domain):
        """Return logo bytes for ``domain``, or ``None`` if all tiers fail.

        Never raises on network/HTTP errors -- logs a warning instead.
        """
        domain = extract_domain(domain)
        if not domain:
            _logger.warning('web_fetch_logo: invalid domain input: %r', domain)
            return None
        for name, step in (
            ('logo.dev', self._fetch_logo_dev),
            ('icon.horse', self._fetch_icon_horse),
            ('google', self._fetch_google),
            ('scrape', self._fetch_scrape),
        ):
            try:
                data = step(domain)
            except Exception as exc:
                _logger.warning('web_fetch_logo: %s failed for %s: %s',
                                name, domain, exc)
                continue
            if data:
                _logger.info('web_fetch_logo: logo for %s from %s (%d bytes)',
                             domain, name, len(data))
                return data
        _logger.warning('web_fetch_logo: no logo source succeeded for %s',
                        domain)
        return None

    # -- tiers --------------------------------------------------------

    def _fetch_logo_dev(self, domain):
        if not self.api_key:
            return None
        return self._get_image(_LOGO_DEV_URL.format(domain=domain),
                               params={'token': self.api_key})

    def _fetch_icon_horse(self, domain):
        return self._get_image(_ICON_HORSE_URL.format(domain=domain))

    def _fetch_google(self, domain):
        return self._get_image(_GOOGLE_FAVICON_URL,
                               params={'domain': domain, 'sz': 128})

    def _fetch_scrape(self, domain):
        url = self._find_logo_url('https://' + domain)
        if not url:
            return None
        return self._get_image(url, sanitize_svg=True)

    # -- helpers ------------------------------------------------------

    def _get_image(self, url, params=None, sanitize_svg=False):
        """Download ``url`` and return image bytes, or ``None``.

        Validates HTTP 200, image/* content-type and a maximum size.
        SVG is kept as-is (raster sources pass through unchanged); when
        ``sanitize_svg`` is set (scrape tier), SVG is sanitized first.
        """
        resp = requests.get(url, params=params, timeout=self.timeout,
                            headers={'User-Agent': USER_AGENT})
        resp.raise_for_status()
        content_type = resp.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            return None
        data = resp.content
        if not data or len(data) > self.max_bytes:
            return None
        if sanitize_svg and self._is_svg(data):
            data = sanitize_svg_xml(data)
            if not data:
                return None
        return data

    @staticmethod
    def _is_svg(data):
        """Cheap SVG detection: raw SVG starts with '<' (XML/SVG root)."""
        return data[:1] == b'<'

    def _find_logo_url(self, url):
        """Parse website HTML for a logo image URL (og:image, touch icon,
        icon/logo links). Returns an absolute URL or ``None``."""
        try:
            resp = requests.get(url, timeout=self.timeout,
                                headers={'User-Agent': USER_AGENT})
            resp.raise_for_status()
            html = resp.text[:SCRAPE_HTML_LIMIT]
        except Exception:
            return None

        candidates = []
        # og:image (both attribute orders)
        candidates += re.findall(
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\' ]+)',
            html)
        candidates += re.findall(
            r'<meta[^>]+content=["\']([^"\' ]+)["\'][^>]+property=["\']og:image["\']',
            html)
        # apple-touch-icon / icon / logo links (both attribute orders)
        candidates += re.findall(
            r'<link[^>]+rel=["\'][^"\']*(?:icon|logo|shortcut)[^"\']*["\'][^>]+href=["\']([^"\' ]+)',
            html)
        candidates += re.findall(
            r'<link[^>]+href=["\']([^"\' ]+)["\'][^>]+rel=["\'][^"\']*(?:icon|logo|shortcut)[^"\']*["\']',
            html)

        for candidate in candidates:
            candidate = candidate.strip()
            if not candidate or candidate.startswith('data:'):
                continue
            return urljoin(url, candidate)
        return None


def fetch_logo(domain, api_key=None, timeout=DEFAULT_TIMEOUT,
               max_bytes=DEFAULT_MAX_BYTES):
    """Fetch a company logo for ``domain`` as raw bytes, or ``None``.

    Tier chain: logo.dev (if ``api_key`` given) -> icon.horse -> Google
    -> HTML scraping. Never raises on fetch failures.
    """
    return LogoFetcher(api_key=api_key, timeout=timeout,
                       max_bytes=max_bytes).fetch(domain)


def fetch_logo_b64(domain, api_key=None, timeout=DEFAULT_TIMEOUT,
                   max_bytes=DEFAULT_MAX_BYTES):
    """Fetch a company logo for ``domain`` as a base64 string, or ``None``.

    The base64 string can be assigned directly to Odoo Binary fields
    (e.g. ``res.partner.image_1920``).
    """
    data = fetch_logo(domain, api_key=api_key, timeout=timeout,
                      max_bytes=max_bytes)
    if not data:
        return None
    return base64.b64encode(data).decode()
