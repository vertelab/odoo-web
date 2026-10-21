# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
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

{
    'name': 'Time Picker Field',
    'summary': 'Touch-friendly time picker widget for float_time fields.',
    'category': 'Extra Tools',
    'author': 'Vertel Sverige AB',
    'contributor': '',
    'maintainer': 'Vertel Sverige AB',
    'repository': 'https://github.com/vertelab/odoo-web',
    'version': '18.0.1.0.1',
    # Version ledger: 18.0 = Odoo version. 1 = Major. Non regressionable code.
    # 0 = Minor. 1 = Bug fixes
    'license': 'AGPL-3',
    'website': 'https://vertel.se/apps/odoo-web/timepicker_field',
    'description': '''
Time Picker Field
=================

    An OWL widget for `float_time` fields that opens a touch-friendly
    hour/minute picker instead of requiring the user to type "HH:MM".

    Ported from Elevata's `elevata_timepicker`. The widget itself was
    already OWL 2 and needed no behavioural change; only the module name,
    the asset paths and the template names changed.

    Features:

        - Hour and minute steppers with 15-minute snapping
        - Native select fallback for keyboard and screen reader users
        - Viewport-aware placement (flips up, clamps horizontally)
        - 44x44 px touch targets per WCAG 2.5.5
        - Closes on outside click

    Usage:

        <field name="duration" widget="timepicker_field"/>
    ''',
    'depends': [
        'web',
    ],
    'assets': {
        'web.assets_backend': [
            'timepicker_field/static/src/scss/timepicker.scss',
            'timepicker_field/static/src/js/timepicker_field.js',
            'timepicker_field/static/src/xml/timepicker_field.xml',
        ],
    },
    'application': False,
    'installable': True,
    'auto_install': False,
}
