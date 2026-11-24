"""Install hook: retire sticky_pivot_view once this module takes over."""

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

SUPERSEDED_MODULE = 'sticky_pivot_view'


def post_init_hook(env):
    """Uninstall ``sticky_pivot_view`` if it is installed.

    The check is the whole point. A hook that uninstalls unconditionally would
    raise on every database that never had the Cybrosys module - and that is
    the normal case, not the exception.

    ``depends`` is ``web``, not ``sticky_pivot_view``, so removing the module
    does not cascade back onto this one. See the manifest for why.

    States handled:

    ``installed``      uninstall it.
    ``to upgrade``     uninstall it; Odoo resolves the pending upgrade first.
    ``to remove``      already queued for removal - leave it alone.
    ``uninstalled``    nothing to do.
    missing            nothing to do.

    The uninstall is done with ``button_immediate_uninstall`` so the database
    is left in a consistent state before the next request. If it raises, the
    exception is logged and swallowed: a failed cleanup must not roll back the
    installation of this module, because then the console error the module
    exists to remove would come back with no way to see why.
    """
    module = env['ir.module.module'].search(
        [('name', '=', SUPERSEDED_MODULE)], limit=1
    )
    if not module:
        _logger.info(
            "%s: %s is not present in this database - nothing to retire.",
            __name__, SUPERSEDED_MODULE,
        )
        return

    if module.state not in ('installed', 'to upgrade'):
        _logger.info(
            "%s: %s is in state '%s' - leaving it alone.",
            __name__, SUPERSEDED_MODULE, module.state,
        )
        return

    _logger.info(
        "%s: %s is installed and is superseded by this module - uninstalling.",
        __name__, SUPERSEDED_MODULE,
    )
    try:
        module.with_user(SUPERUSER_ID).button_immediate_uninstall()
    except Exception:  # noqa: BLE001 - cleanup must not break the install
        _logger.exception(
            "%s: could not uninstall %s. The module is still installed and its "
            "extension still loads in web.assets_backend, so the console will "
            "keep reporting 'Missing (extension) parent templates'. Uninstall "
            "it manually: checkmodule -d <db> -m %s -U",
            __name__, SUPERSEDED_MODULE, SUPERSEDED_MODULE,
        )
        return

    _logger.info("%s: %s uninstalled.", __name__, SUPERSEDED_MODULE)
