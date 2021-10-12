# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "Web Backend Tema AF V12",
    "summary": "Web Backend Theme AF V12	",
    "version": "12.0.1.1.4",
    "category": "Theme/Backend",
    "description": """
		Web Backend tema AF för Odoo 12.0 community edition. With New CSS \n
		v 12.0.1.0.8 New update from Jonas  github.com jonasnyhav odoo-web tree Dev-12.0-CSS-from-Jonas \n 
		v 12.0.1.0.9 Added hoover and selected css to menu item  \n 
		v 12.0.1.1.0 changed css for primary and secondary buttons \n
		v 12.0.1.1.1 Added css weight bold on selected app. Removed unnecessary code\n
		v 12.0.1.1.2 Changed colors of navlinks\n
		v 12.0.1.1.3 AFC-2836 changed the padding of label that ended up under buttons\n
		v 12.0.1.1.4 AFC-2860 fixe overlapping problem with div af_apps_sidebar_panel\n  
    """,
    "author": "Vertel AB",
    "license": "LGPL-3",
    "installable": True,
    "depends": [
        'web_editor'
    ],
    "qweb": [
        "static/src/xml/*.xml",
    ],
    "data": [
        'views/assets.xml',
        "views/web.xml"
    ]
}
