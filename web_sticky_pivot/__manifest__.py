{
    'name': 'Web: Sticky Pivot View',
    'version': '18.0.1.0.2',
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

Relationship to sticky_pivot_view
---------------------------------

This module supersedes ``sticky_pivot_view``. Both extensions cannot be active
at once: they target the same template and would apply the sticky CSS twice.

``depends`` is deliberately ``web`` and not ``sticky_pivot_view``. Depending on
the module we are about to remove would make the uninstall cascade back onto
this module, and we would remove ourselves along with it.

On install, ``post_init_hook`` checks whether ``sticky_pivot_view`` is present
and installed. If it is, it is uninstalled; if it is not, the hook does
nothing. The check is the point - a hook that uninstalls unconditionally would
fail on every database that never had the Cybrosys module.

``auto_install`` is False: the module is installed deliberately, once per
database, because it performs a destructive step.
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
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'auto_install': False,
    'application': False,
}
