# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "Web Backend Tema AF V12",
    "summary": "Web Backend Theme AF V12	",
    "version": "12.0.1.0.8",
    "category": "Theme/Backend",
    "description": """
		Web Backend tema AF för Odoo 12.0 community edition. With New CSS
    """,
    "author": "Vertel AB",
    "license": "LGPL-3",
    "installable": True,
    "depends": [
        'web'
    ],
    "qweb": [
        "static/src/xml/*.xml",
    ],
    "data": [
        'views/assets.xml',
        "views/web.xml"
    ]
}
