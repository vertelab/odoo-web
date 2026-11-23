{
    'name': 'Web: Sticky Pivot View',
    'version': '18.0.1.0.1',
    'category': 'Hidden/Tools',
    'summary': "Sticky pivot headers and first column, without breaking the lazy pivot bundle",
    'description': '''
Sticky Pivot View
=================

Makes the pivot view header stick during vertical scroll and the first column
stick during horizontal scroll.

Why this module exists
----------------------

The third-party module ``sticky_pivot_view`` (Cybrosys) registers its template
extension in ``web.assets_backend``. In Odoo 18 the pivot view was moved to the
lazy bundle:

    web/__manifest__.py
        'web.assets_backend': [..., ('remove', 'web/static/src/views/pivot/**')]
        'web.assets_backend_lazy': [..., 'web/static/src/views/pivot/**']

The parent template ``web.PivotRenderer`` therefore does not exist in
``web.assets_backend`` any more, and the browser console reports:

    Missing (extension) parent templates: web.PivotRenderer

Regenerating assets does not help: the error is not a cache problem, it is a
wrong bundle. This module places the same extension in
``web.assets_backend_lazy``, next to the template it inherits from, and drops
the ``t-name`` attribute (an extension must not register itself as a primary
template).

This module does not replace ``sticky_pivot_view``; it supersedes it. Install
this one and uninstall the other, otherwise both extensions load and the
behaviour is applied twice.
    ''',
    'author': 'Vertel AB',
    'website': 'https://vertel.se/apps/odoo-web/web_sticky_pivot',
    'license': 'LGPL-3',
    'depends': [
        'web',
    ],
    'assets': {
        'web.assets_backend_lazy': [
            'web_sticky_pivot/static/src/css/sticky_pivot.css',
            'web_sticky_pivot/static/src/xml/sticky_pivot.xml',
        ],
    },
    'installable': True,
    'auto_install': True,
    'application': False,
}
