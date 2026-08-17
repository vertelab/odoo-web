# -*- coding: utf-8 -*-
# Copyright (C) 2026 Vertel AB
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import json

from html import escape

from odoo import http
from odoo.http import request, Response
from odoo.tools import ustr

# ---------------------------------------------------------------------------
# Ärvd backend-manifest-override. Vi ärver OCA:s WebManifest-klass (som i sin
# tur ärver Odoos) och dekorrerar om samma route — OCA gör exakt detta mot
# Odoos web-manifest, och vår modul laddas efter web_pwa_customize (depends).
# ---------------------------------------------------------------------------
try:
    from odoo.addons.web_pwa_customize.controllers.webmanifest import (
        WebManifest as OcaWebManifest,
    )
except Exception:  # pragma: no cover
    OcaWebManifest = None

_PWA_ICON_URL_BASE = '/web_pwa_push/icon'

# ---------------------------------------------------------------------------
# Service worker — pass-through + push-listener.
# Ingen cache: respekterar sidors Cache-Control: no-store (t.ex. /ai/chat).
# Scope för /ai/ kontrolleras via headern Service-Worker-Allowed (sätts i
# route-metoden).
# ---------------------------------------------------------------------------
_SW_JS = r"""// PWA Push — pass-through service worker
// Ingen cache: respekterar no-store-sidor (t.ex. /ai/chat).
self.addEventListener('install', (event) => {
    self.skipWaiting();
});
self.addEventListener('activate', (event) => {
    event.waitUntil(self.clients.claim());
});
self.addEventListener('fetch', (event) => {
    event.respondWith(fetch(event.request));
});
self.addEventListener('push', (event) => {
    if (!event.data) return;
    let notification;
    try {
        notification = event.data.json();
    } catch (e) {
        notification = { title: 'Odoo', body: event.data.text() };
    }
    const options = Object.assign({}, notification.options || {});
    options.data = options.data || {};
    options.icon = options.icon || '/web_pwa_push/icon192x192.png';
    options.badge = options.badge || '/web_pwa_push/icon192x192.png';
    event.waitUntil(self.registration.showNotification(notification.title || 'Odoo', options));
});
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    const url = (event.notification.data && event.notification.data.url) || '/ai/chat';
    event.waitUntil(clients.matchAll({ type: 'window', includeUncontrolled: true }).then((list) => {
        for (const client of list) {
            if ('focus' in client) {
                client.focus();
                if ('navigate' in client) client.navigate(url);
                return;
            }
        }
        return clients.openWindow(url);
    }));
});
self.addEventListener('pushsubscriptionchange', async (event) => {
    if (!event.oldSubscription) return;
    const subscription = await self.registration.pushManager.subscribe(event.oldSubscription.options);
    await fetch('/web/dataset/call_kw/mail.push.device/register_devices', {
        headers: { 'Content-type': 'application/json' },
        body: JSON.stringify({
            id: 1, jsonrpc: '2.0', method: 'call',
            params: {
                model: 'mail.push.device', method: 'register_devices', args: [],
                kwargs: { ...subscription.toJSON(), previousEndpoint: event.oldSubscription.endpoint },
                context: {},
            },
        }),
        method: 'POST', mode: 'cors', credentials: 'include',
    });
});
"""


class PwaController(http.Controller):

    # ------------------------------------------------------------------
    # Service worker (kontrollerar /ai/ via Service-Worker-Allowed)
    # ------------------------------------------------------------------
    @http.route('/pwa/sw.js', type='http', auth='public', methods=['GET'], sitemap=False)
    def pwa_sw(self):
        return Response(
            _SW_JS,
            headers=[
                ('Content-Type', 'text/javascript'),
                ('Cache-Control', 'no-store, must-revalidate'),
                ('Service-Worker-Allowed', '/ai/'),
            ])

    # ------------------------------------------------------------------
    # Chat-appens manifest (start_url/scope definierar appen, inte URL:en)
    # ------------------------------------------------------------------
    @http.route('/pwa/manifest/ai-chat', type='http', auth='public', methods=['GET'], sitemap=False)
    def pwa_manifest_ai_chat(self):
        company = request.env.company.sudo()
        manifest = {
            'name': company.pwa_app_name('chat'),
            'short_name': company.pwa_app_name('chat')[:12],
            'start_url': '/ai/chat',
            'scope': '/ai/',
            'display': 'standalone',
            'background_color': self._pwa_color('background'),
            'theme_color': self._pwa_color('theme'),
            'icons': [
                {'src': '/web_pwa_push/icon192x192.png', 'sizes': '192x192', 'type': 'image/png'},
                {'src': '/web_pwa_push/icon512x512.png', 'sizes': '512x512', 'type': 'image/png',
                 'purpose': 'any maskable'},
            ],
        }
        return request.make_json_response(manifest, {
            'Content-Type': 'application/manifest+json'})

    # ------------------------------------------------------------------
    # Publik VAPID-nyckel — för push-registrering från fristående sidor
    # (t.ex. /ai/chat). Nyckeln är publik av design.
    # ------------------------------------------------------------------
    @http.route('/pwa/vapid-public-key', type='http', auth='public', methods=['GET'], sitemap=False)
    def pwa_vapid_public_key(self):
        key = request.env['mail.push.device'].sudo().get_web_push_vapid_public_key()
        return request.make_json_response({'vapid_public_key': key})

    # ------------------------------------------------------------------
    # Install-hubb (generisk, valfri) — lista registrerade appar
    # ------------------------------------------------------------------
    @http.route('/pwa/install', type='http', auth='public', methods=['GET'], sitemap=False)
    def pwa_install(self, **kw):
        company = request.env.company.sudo()
        apps = self._pwa_install_apps(company)
        cards = '\n'.join(self._pwa_install_card(app) for app in apps)
        html = _INSTALL_HTML.replace('<!-- APP_CARDS -->', cards)
        return Response(html, headers=[
            ('Content-Type', 'text/html; charset=utf-8'),
            ('Cache-Control', 'no-store, must-revalidate')])

    def _pwa_install_apps(self, company):
        """Registrerade appar. Primär: AI-chatten. Sekundär: backend (som
        webbsida — Odoos inbyggda install-app vid /odoo)."""
        return [
            {
                'key': 'ai-chat',
                'title': company.pwa_app_name('chat'),
                'desc': 'AI-medarbetarna i fickan',
                'manifest': '/pwa/manifest/ai-chat',
                'href': '/ai/chat',
                'icon': '/web_pwa_push/icon192x192.png',
            },
            {
                'key': 'odoo',
                'title': company.pwa_app_name('backend'),
                'desc': 'Hela Odoo som app',
                'manifest': '/web/manifest.webmanifest',
                'href': '/odoo',
                'icon': '/web_pwa_push/icon192x192.png',
            },
        ]

    def _pwa_install_card(self, app):
        return """
        <div class="app-card" data-manifest="%s" data-href="%s">
            <img class="app-icon" src="%s" alt="%s"/>
            <div class="app-info">
                <div class="app-title">%s</div>
                <div class="app-desc">%s</div>
            </div>
            <button class="install-btn" type="button">Installera</button>
            <a class="open-link" href="%s">Öppna</a>
        </div>
        """ % (escape(app['manifest']), escape(app['href']), escape(app['icon']),
               escape(app['title']), escape(app['title']), escape(app['desc']),
               escape(app['href']))

    def _pwa_color(self, kind):
        key = 'pwa.manifest.%s_color' % kind
        return request.env['ir.config_parameter'].sudo().get_param(key, '#1a1a2e')


if OcaWebManifest is not None:
    class WebManifest(OcaWebManifest):
        """Kundbrandat backend-manifest (/web/manifest.webmanifest).

        Ärver OCA:s klass (route ärvs — samma mönster som OCA mot Odoo) men
        anropar Odoos ORIGINAL webmanifest (OCA:s letar hårdkodat efter
        /web_pwa_customize/icon) och applicerar branding med vår ikon-base.
        """

        @http.route('/web/manifest.webmanifest', type='http', auth='public',
                    methods=['GET'], readonly=True)
        def webmanifest(self):
            from odoo.addons.web.controllers.webmanifest import WebManifest as OdooWebManifest
            # super(OcaWebManifest, self) → Odoos original (OcaWebManifest ärver Odoos)
            res = super(OcaWebManifest, self).webmanifest()
            manifest = json.loads(res.response[0])
            icp = request.env['ir.config_parameter'].sudo()
            manifest['name'] = request.env.company.sudo().pwa_app_name('backend')
            manifest['short_name'] = icp.get_param(
                'pwa.manifest.short_name', manifest.get('name', 'Odoo'))
            manifest['background_color'] = icp.get_param(
                'pwa.manifest.background_color', '#714B67')
            manifest['theme_color'] = icp.get_param(
                'pwa.manifest.theme_color', '#714B67')
            pwa_icon = request.env['ir.attachment'].sudo().search(
                [('url', 'like', _PWA_ICON_URL_BASE + '.')], limit=1)
            if pwa_icon:
                manifest['icons'] = self._get_pwa_manifest_icons(pwa_icon)
            body = json.dumps(manifest, default=ustr)
            return request.make_response(body, [
                ('Content-Type', 'application/manifest+json')])

        def _get_pwa_manifest_icons(self, pwa_icon):
            """Samma mönster som OCA men med vår ikon-base (/web_pwa_push/icon)."""
            icons = []
            if not pwa_icon.mimetype.startswith('image/svg'):
                all_icons = request.env['ir.attachment'].sudo().search([
                    ('url', 'like', _PWA_ICON_URL_BASE),
                    ('url', 'not like', _PWA_ICON_URL_BASE + '.'),
                ])
                for icon in all_icons:
                    icon_size_name = icon.url.split('/')[-1].lstrip('icon').split('.')[0]
                    icons.append({
                        'src': icon.url,
                        'sizes': icon_size_name,
                        'type': icon.mimetype,
                    })
            else:
                icons = [{
                    'src': pwa_icon.url,
                    'sizes': '128x128 144x144 152x152 192x192 256x256 512x512',
                    'type': pwa_icon.mimetype,
                }]
            return icons


# ---------------------------------------------------------------------------
# Install-hubb HTML (lätt, generisk). Manuella vägen är ALLTID synlig —
# prompten är en lyx, inte en förutsättning (lärdom från ai-chat-pwa-testet).
# ---------------------------------------------------------------------------
_INSTALL_HTML = r"""<!DOCTYPE html>
<html lang="sv">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no"/>
<title>Installera appar</title>
<style>
:root { --bg:#fff; --card:#f5f7fa; --border:#e0e0e0; --text:#1a1a2e; --muted:#666;
        --accent:#1976d2; --radius:12px;
        --font:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; }
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:var(--font); background:var(--bg); color:var(--text);
       min-height:100vh; display:flex; align-items:center; justify-content:center; padding:24px; }
.container { width:100%; max-width:440px; }
h1 { font-size:22px; margin-bottom:4px; }
.sub { color:var(--muted); font-size:14px; margin-bottom:20px; }
.app-card { background:var(--card); border:1px solid var(--border); border-radius:var(--radius);
            padding:16px; display:flex; align-items:center; gap:14px; margin-bottom:12px; }
.app-icon { width:56px; height:56px; border-radius:12px; object-fit:cover; background:#fff; }
.app-info { flex:1; }
.app-title { font-weight:600; font-size:16px; }
.app-desc { color:var(--muted); font-size:13px; }
.install-btn { background:var(--accent); color:#fff; border:none; border-radius:8px;
               padding:8px 14px; font-size:14px; font-weight:600; cursor:pointer; }
.open-link { color:var(--accent); font-size:14px; text-decoration:none; }
.note { margin-top:16px; color:var(--muted); font-size:13px; line-height:1.5; }
.ios-step { display:flex; align-items:center; gap:8px; margin-top:8px; }
.kbd { background:#fff; border:1px solid var(--border); border-radius:6px; padding:2px 8px;
       font-size:12px; font-weight:600; }
</style>
</head>
<body>
<div class="container">
<h1>Installera appar</h1>
<div class="sub">Lägg apparna på hemskärmen — precis som en vanlig app.</div>
<!-- APP_CARDS -->
<div class="note">
<div><b>Android:</b> tryck <b>Installera</b> — eller webbläsarmenyn <span class="kbd">⋮</span> → <b>Installera app</b>.</div>
<div class="ios-step"><b>iPhone:</b> <span class="kbd">Dela</span> → <b>Lägg till på hemskärmen</b>.</div>
</div>
</div>
<script>
(function () {
    var isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent);
    var deferredPrompt = null;

    window.addEventListener('beforeinstallprompt', function (e) {
        e.preventDefault();
        deferredPrompt = e;
        var btns = document.querySelectorAll('.install-btn');
        for (var i = 0; i < btns.length; i++) btns[i].style.display = 'inline-block';
    });

    var installBtns = document.querySelectorAll('.install-btn');
    for (var j = 0; j < installBtns.length; j++) {
        installBtns[j].addEventListener('click', function () {
            if (!deferredPrompt) return;
            deferredPrompt.prompt();
            deferredPrompt.userChoice.then(function () { deferredPrompt = null; });
        });
    }

    if (isIOS) {
        for (var k = 0; k < installBtns.length; k++) installBtns[k].style.display = 'none';
    }

    // Installerad-status (Android/Chrome; progressiv förbättring)
    if (navigator.getInstalledRelatedApps) {
        navigator.getInstalledRelatedApps().then(function (apps) {
            var cards = document.querySelectorAll('.app-card');
            for (var c = 0; c < cards.length; c++) {
                var href = cards[c].getAttribute('data-href');
                for (var a = 0; a < apps.length; a++) {
                    if (apps[a].id === location.origin + href) {
                        cards[c].querySelector('.app-title').textContent += ' ✓';
                    }
                }
            }
        }).catch(function () {});
    }
})();
</script>
</body>
</html>
"""
