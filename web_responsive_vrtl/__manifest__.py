# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo SA, Open Source Management Solution, third party addon
#    Copyright (C) 2021- Vertel AB (<https://vertel.se>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name": "Web Responsive Vrtl",
    "summary": "A responsive theme for the Odoo backend",
    "version": "14.0.1.2.2",
    "category": "Themes/Backend",
    "website": "https://github.com/vertelab",
    'description': """
    This module provides a modern and responsive theme for the Odoo backend,
    improving the user experience and making it more intuitive and enjoyable.
    """,
    "author": "Vertel AB",
    "license": "LGPL-3",
    "installable": True,
    "depends": ["web", "mail"],
    "data": [
    "data/resources.xml",
    "views/assets.xml",
    "views/res_users.xml",
    "views/web.xml",  
    ],
    "qweb": [
        "static/src/xml/apps.xml",
        "static/src/xml/form_buttons.xml",
        "static/src/xml/navbar.xml",
        "static/src/xml/attachment_viewer.xml",
        "static/src/xml/discuss.xml",
        "static/src/xml/control_panel.xml",
        "static/src/xml/search_panel.xml",
        "static/src/xml/menu.xml",
    ],
    "sequence": 1,
}
