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
* On install, uninstalls ``sticky_pivot_view`` if it is present and installed.

Relationship to sticky_pivot_view
=================================

This module supersedes ``sticky_pivot_view``. Both extensions cannot be active
at once: they target the same template and would apply the sticky CSS twice.

``depends`` is deliberately ``web`` and not ``sticky_pivot_view``. Depending on
the module we are about to remove would make the uninstall cascade back onto
this module, and we would remove ourselves along with it.

``auto_install`` is False. The module is installed deliberately, once per
database, because it performs a destructive step.

Install
=======

::

    checkmodule -d <database> -m web_sticky_pivot

The ``post_init_hook`` then checks ``sticky_pivot_view``:

============================  ==========================================
State of sticky_pivot_view    Hook does
============================  ==========================================
missing                       nothing
``uninstalled``               nothing
``to remove``                 nothing (already queued)
``installed``                 uninstalls it
``to upgrade``                uninstalls it
============================  ==========================================

If the uninstall raises, the exception is logged and swallowed. A failed
cleanup must not roll back the installation of this module — then the console
error the module exists to remove would come back with no way to see why. The
log line names the manual command.

Verified
========

Tested on Odoo 18.0-20261123 against a copy of the production database:

* hook with no ``sticky_pivot_view`` present → logs, does nothing
* hook with ``sticky_pivot_view`` installed → uninstalls it, this module stays
* hook with ``sticky_pivot_view`` in ``to remove`` → leaves it alone
* pivot view renders with no console error
* ``.o_sticky_pivot_head`` → ``position: sticky``, ``top: 0px``
* ``.o_sticky_pivot_first_col`` → ``position: sticky``, ``left: 0px``

Credits
=======

Behaviour modelled on ``sticky_pivot_view`` by Cybrosys Technologies
(LGPL-3). This module is a rewrite for the Odoo 18 asset layout.
