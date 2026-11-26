# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'LMS: Reading Design',
    'version': '18.0.1.0.0',
    'summary': 'Readable, permanent styling for eLearning courses on the website.',
    'category': 'Website/eLearning',
    'author': 'Vertel Sverige AB',
    'website': 'https://vertel.se/apps/odoo-web/lms_reading_design',
    'license': 'AGPL-3',
    'maintainer': 'Vertel Sverige AB',
    'description': '''
LMS: Reading Design
===================

Makes eLearning courses readable and pleasant to look at, and keeps them that
way through upgrades.

Why it exists
-------------
Course slides carry their own HTML in module data. A section can therefore end
up with a dark background colour while still claiming the light colour
combination (`o_cc1`), which paints near-black text on a dark blue cover. That
combination measured **1.94:1** — well below the 4.5:1 required by WCAG AA.
In fullscreen the slide sits on a dark gradient (`#1f262d`), where black text
measured **1.01:1**, i.e. effectively invisible.

What it does
------------
1. **Guarantees readable text on covers.** Any `s_cover` that carries a dark
   background gets light text, whatever colour combination the slide claims.
   A slide can no longer paint itself unreadable.
2. **A proper reading surface.** The fullscreen player gets a light "paper"
   page with comfortable measure, generous line height and clear heading
   hierarchy, so long lessons read like a document rather than a wall of text.
3. **A calmer palette.** Deep blue-green primary, warm accent, rounded cards
   and softer section rhythm instead of Odoo's flat default.

Where the styling lives
-----------------------
The SCSS ships **in this module** (`static/src/scss/`), not in the website's
custom CSS files. Those files live in Odoo's own package directory and are
overwritten by any Odoo upgrade — a redesign placed there would silently
disappear. Module assets are re-applied on every upgrade by definition.

Nothing here is written to the database, so no content can be lost.
    ''',
    'depends': [
        'website_slides',
    ],
    'data': [
        'views/assets.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'lms_reading_design/static/src/scss/lms_reading_design.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
