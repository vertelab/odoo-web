# Copyright (C) 2026 Vertel Sverige AB (<https://vertel.se>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'LMS: Reading Design',
    'version': '18.0.1.10.0',
    'summary': 'Readable, Swedish eLearning courses on the website.',
    'category': 'Website/eLearning',
    'author': 'Vertel Sverige AB',
    'website': 'https://vertel.se/apps/odoo-web/lms_reading_design',
    'license': 'AGPL-3',
    'maintainer': 'Vertel Sverige AB',
    'description': '''
LMS: Reading Design
===================

Makes eLearning courses readable, Swedish and pleasant to look at — and keeps
them that way through upgrades.

Why it exists
-------------
Course slides carry their own HTML in module data. A section can therefore end
up with a dark background colour while still claiming the light colour
combination (o_cc1), which paints near-black text on a dark blue cover. That
combination measured 1.94:1 — well below the 4.5:1 required by WCAG AA. In
fullscreen the slide sits on a dark gradient, where black text measured 1.01:1,
i.e. effectively invisible.

What it does
------------
1. Guarantees readable text on covers, whatever colour combination a slide
   claims.
2. Gives the fullscreen player a proper reading page, and gives the quiz the
   same page as the articles instead of Odoo's 1140px bootstrap container.
3. Translates the quiz invitation to Swedish and drops the "+ 100 XP" badge,
   which means nothing to a course participant here.
4. A calmer palette: deep blue-green primary, warm accent, rounded cards.

Where it lives
--------------
The SCSS and the quiz templates ship in this module, not in the website's
custom CSS files. Those live inside Odoo's package directory and are
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
            'lms_reading_design/static/src/js/quiz_validation_sv.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
