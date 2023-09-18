# Copyright 2016 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Vertel Web Timeline Fix",
    "summary": "Interactive visualization chart to show events in time",
    "version": "16.0.0.0.1",
    "author": "Vertel AB",
    "category": "web",
    "license": "AGPL-3",
    "website": "https://github.com/vertel/odoo-web",
    "depends": ["web_timeline"],
    "assets": {
        "web.assets_backend": [
            "web_timeline_fix/static/src/js/timeline_controller_esm.js",
        ],
    },
}
