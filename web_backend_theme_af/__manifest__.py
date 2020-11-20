# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "Web Backend Tema AF V12",
    "summary": "Web Backend Theme AF V12	",
    "version": "12.0.0.6",
    "category": "Theme/Backend",
    "description": """
		Web Backend tema AF för Odoo 12.0 community edition.
    """,
    "author": "Vertel AB",
    "license": "LGPL-3",
    "installable": True,
    "depends": [
        'portal', 'web'
    ],
    "qweb": [
        "static/src/xml/*.xml",
    ],
    "data": [
        'views/assets.xml',
        'views/template.xml',
        "views/web.xml"
    ]
}
