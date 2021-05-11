# -*- coding: UTF-8 -*-

##############################################################################
#
#    Odoo, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2021 Vertel AB (<http://vertel.se>).
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
# Version format OdooMajor.OdooMinor.Major.Minor.Patch
{
    'name': 'Web XMLID Class',
    'version': '12.0.1.0.0',
    'category': 'Web',
    'description': """
Web XMLID Class
===============================================================================
This module adds the xml id of a view as the class of the html body.\n
v12.0.1.0.0 AFC-2022: Created module. \n""",
    'author': "Vertel AB",
    'license': 'AGPL-3',
    'website': 'https://www.vertel.se',
    "depends": [
        'web',
    ],
    'data': [
        'views/assets.xml'
    ],
    'installable': True,
}
