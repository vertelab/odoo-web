# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import base64
from unittest.mock import Mock, patch

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.web_fetch_logo.models.logo_fetcher import (
    LogoFetcher,
    extract_domain,
    fetch_logo,
    fetch_logo_b64,
    sanitize_svg_xml,
)

PNG = b'\x89PNG\r\n\x1a\n' + b'0' * 100
SVG = (b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
       b'<rect width="10" height="10" fill="red"/></svg>')


def _img_response(data=PNG, content_type='image/png', headers=None):
    resp = Mock()
    resp.status_code = 200
    resp.content = data
    resp.headers = headers or {'Content-Type': content_type}
    resp.text = data.decode('utf-8', errors='replace')
    resp.raise_for_status = Mock()
    return resp


def _http_error():
    import requests
    exc = requests.exceptions.HTTPError('404 Client Error')
    resp = Mock()
    resp.raise_for_status = Mock(side_effect=exc)
    return resp


@tagged('-at_install', 'post_install')
class TestLogoFetcher(TransactionCase):

    # -- domain extraction -------------------------------------------

    def test_extract_domain(self):
        cases = {
            'https://www.hetzner.com/pricing': 'hetzner.com',
            'https://hetzner.com': 'hetzner.com',
            'www.hetzner.com': 'hetzner.com',
            'hetzner.com': 'hetzner.com',
            'https://user:pass@sub.example.com:8443/x': 'sub.example.com',
        }
        for source, expected in cases.items():
            self.assertEqual(extract_domain(source), expected, source)
        for bad in ('', None, 'not a domain', 'localhost', '   '):
            self.assertEqual(extract_domain(bad), '', bad)

    # -- tier chain ---------------------------------------------------

    def test_logo_dev_first_when_key_given(self):
        with patch(
            'odoo.addons.web_fetch_logo.models.logo_fetcher.requests.get',
            side_effect=[_img_response(SVG, 'image/svg+xml')]
        ) as mock_get:
            data = fetch_logo('hetzner.com', api_key='pk_test')
        self.assertEqual(data, SVG)
        self.assertEqual(mock_get.call_count, 1)
        url = mock_get.call_args[0][0]
        self.assertIn('img.logo.dev', url)

    def test_logo_dev_skipped_without_key(self):
        with patch(
            'odoo.addons.web_fetch_logo.models.logo_fetcher.requests.get',
            side_effect=[_img_response()]
        ) as mock_get:
            data = fetch_logo('hetzner.com')
        self.assertEqual(data, PNG)
        self.assertEqual(mock_get.call_count, 1)
        url = mock_get.call_args[0][0]
        self.assertIn('icon.horse', url)

    def test_fallback_through_chain(self):
        """logo.dev 404 -> icon.horse 404 -> google 404 -> scrape succeeds."""
        html_with_icon = (b'<html><head>'
                          b'<link rel="icon" href="/logo.svg">'
                          b'</head></html>')
        with patch(
            'odoo.addons.web_fetch_logo.models.logo_fetcher.requests.get',
            side_effect=[
                _http_error(),  # logo.dev
                _http_error(),  # icon.horse
                _http_error(),  # google
                _img_response(html_with_icon, 'text/html'),  # scrape: html
                _img_response(SVG, 'image/svg+xml'),         # scrape: logo
            ]
        ) as mock_get:
            data = fetch_logo('hetzner.com', api_key='pk_test')
        # scraped SVG is sanitized (re-serialized) before being returned
        self.assertEqual(data, sanitize_svg_xml(SVG))
        self.assertEqual(mock_get.call_count, 5)
        # tier order: icon.horse and google were tried before scraping
        self.assertIn('icon.horse', mock_get.call_args_list[1][0][0])
        self.assertIn('s2/favicons', mock_get.call_args_list[2][0][0])

    def test_all_tiers_fail_returns_none(self):
        with patch(
            'odoo.addons.web_fetch_logo.models.logo_fetcher.requests.get',
            side_effect=[_http_error(), _http_error(), _http_error(),
                         _http_error()]
        ):
            self.assertIsNone(fetch_logo('hetzner.com'))

    def test_non_image_content_type_skipped(self):
        """A 200 with text/html is not accepted as a logo."""
        with patch(
            'odoo.addons.web_fetch_logo.models.logo_fetcher.requests.get',
            side_effect=[
                _img_response(b'<html>', 'text/html'),  # logo.dev
                _img_response(),                        # icon.horse
            ]
        ) as mock_get:
            data = fetch_logo('hetzner.com', api_key='pk_test')
        self.assertEqual(data, PNG)
        self.assertEqual(mock_get.call_count, 2)

    def test_size_cap_moves_to_next_tier(self):
        # first tier returns an image above the cap, second tier fits exactly
        oversized = _img_response(PNG + b'0' * 20, content_type='image/png')
        with patch(
            'odoo.addons.web_fetch_logo.models.logo_fetcher.requests.get',
            side_effect=[oversized, _img_response()]
        ) as mock_get:
            data = LogoFetcher(api_key='pk_test',
                               max_bytes=len(PNG)).fetch('hetzner.com')
        self.assertEqual(data, PNG)
        self.assertEqual(mock_get.call_count, 2)

    # -- return contract ----------------------------------------------

    def test_fetch_logo_b64_returns_base64(self):
        with patch(
            'odoo.addons.web_fetch_logo.models.logo_fetcher.requests.get',
            side_effect=[_img_response(PNG)]
        ):
            result = fetch_logo_b64('hetzner.com')
        self.assertEqual(result, base64.b64encode(PNG).decode())
        # decodes back to the raw bytes
        self.assertEqual(base64.b64decode(result), PNG)

    def test_fetch_logo_b64_none_on_failure(self):
        with patch(
            'odoo.addons.web_fetch_logo.models.logo_fetcher.requests.get',
            side_effect=[_http_error(), _http_error(), _http_error(),
                         _http_error()]
        ):
            self.assertIsNone(fetch_logo_b64('hetzner.com'))

    # -- svg sanitizer ------------------------------------------------

    def test_sanitize_svg_removes_active_content(self):
        evil = (b'<svg xmlns="http://www.w3.org/2000/svg" '
                b'onload="alert(1)"><script>alert(2)</script>'
                b'<rect width="10" height="10"/></svg>')
        cleaned = sanitize_svg_xml(evil)
        self.assertIsNotNone(cleaned)
        self.assertNotIn(b'script', cleaned)
        self.assertNotIn(b'onload', cleaned)

    def test_sanitize_svg_removes_javascript_href(self):
        evil = (b'<svg xmlns="http://www.w3.org/2000/svg">'
                b'<a href="javascript:alert(1)"><rect width="10" height="10"/></a>'
                b'</svg>')
        cleaned = sanitize_svg_xml(evil)
        self.assertIsNotNone(cleaned)
        self.assertNotIn(b'javascript:', cleaned)

    def test_sanitize_svg_keeps_clean_svg(self):
        cleaned = sanitize_svg_xml(SVG)
        self.assertIsNotNone(cleaned)
        # content preserved (serialization may differ, e.g. explicit close tags)
        self.assertIn(b'<svg', cleaned)
        self.assertIn(b'<rect', cleaned)
        self.assertIn(b'width="10"', cleaned)
        self.assertNotIn(b'ns0', cleaned)

    def test_sanitize_svg_rejects_unparsable(self):
        self.assertIsNone(sanitize_svg_xml(b'not xml at all <><'))

    # -- scrape: scraped svg is sanitized -----------------------------

    def test_scraped_svg_is_sanitized(self):
        evil_svg = (b'<svg xmlns="http://www.w3.org/2000/svg">'
                    b'<script>alert(1)</script><rect width="10" height="10"/></svg>')
        with patch(
            'odoo.addons.web_fetch_logo.models.logo_fetcher.requests.get',
            side_effect=[
                _img_response(b'<html><head><link rel="icon" '
                              b'href="/logo.svg"></head></html>',
                              'text/html'),
                _img_response(evil_svg, 'image/svg+xml'),
            ]
        ) as mock_get:
            data = LogoFetcher()._fetch_scrape('hetzner.com')
        self.assertIsNotNone(data)
        self.assertNotIn(b'script', data)


@tagged('-at_install', 'post_install')
class TestWebFetchLogoMixin(TransactionCase):

    def test_mixin_uses_config_api_key(self):
        self.env['ir.config_parameter'].set_param(
            'web_fetch_logo.logo_dev_api_key', 'pk_mixin')
        with patch(
            'odoo.addons.web_fetch_logo.models.logo_fetcher.requests.get',
            side_effect=[_img_response(SVG, 'image/svg+xml')]
        ) as mock_get:
            result = self.env['web.fetch.logo.mixin'].fetch_logo_b64(
                'hetzner.com')
        self.assertEqual(result, base64.b64encode(SVG).decode())
        self.assertIn('img.logo.dev', mock_get.call_args[0][0])

    def test_mixin_without_key_skips_logo_dev(self):
        self.env['ir.config_parameter'].set_param(
            'web_fetch_logo.logo_dev_api_key', '')
        with patch(
            'odoo.addons.web_fetch_logo.models.logo_fetcher.requests.get',
            side_effect=[_img_response()]
        ) as mock_get:
            result = self.env['web.fetch.logo.mixin'].fetch_logo_b64(
                'hetzner.com')
        self.assertEqual(result, base64.b64encode(PNG).decode())
        self.assertIn('icon.horse', mock_get.call_args[0][0])
