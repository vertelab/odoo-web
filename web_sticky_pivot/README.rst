=====================
Web: Sticky Pivot View
=====================

Sticky pivot headers and first column for Odoo 18.

Why
===

The third-party module ``sticky_pivot_view`` (Cybrosys) registers its template
extension in ``web.assets_backend``. Odoo 18 moved the pivot view to the lazy
bundle::

    'web.assets_backend': [..., ('remove', 'web/static/src/views/pivot/**')]
    'web.assets_backend_lazy': [..., 'web/static/src/views/pivot/**']

The parent template ``web.PivotRenderer`` is therefore not present in
``web.assets_backend``, and the browser console reports::

    Missing (extension) parent templates: web.PivotRenderer

Regenerating assets does not help — the error is a wrong bundle, not a cache.

What this module does
=====================

* Loads the extension from ``web.assets_backend_lazy``, next to its parent.
* Drops ``t-name`` so the extension does not register itself as a primary
  template.
* Uses ``o_sticky_pivot_*`` class names so it cannot collide with the
  ``cb_*`` classes of the module it supersedes.

Migration
=========

Install this module, then uninstall ``sticky_pivot_view``. Both extensions
applied at once would double the CSS.

``auto_install`` is True: the module activates itself when ``web`` is present,
which is always. That is intentional — the fix should not depend on somebody
remembering to install it.

Credits
=======

Behaviour modelled on ``sticky_pivot_view`` by Cybrosys Technologies
(LGPL-3). This module is a rewrite for the Odoo 18 asset layout.
