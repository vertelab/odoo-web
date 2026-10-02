/** @odoo-module **/
// Copyright 2017 - 2018 Modoolar <info@modoolar.com>
// Copyright 2018 Brainbean Apps
// Copyright 2020 CorporateHub (https://corporatehub.eu)
// License LGPLv3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

import { registry } from "@web/core/registry";

/**
 * Handle 'ir.actions.act_view_reload' actions by reloading the currently
 * displayed view.
 *
 * Odoo 14 patched ActionManager._handleAction; Odoo 18 replaces that with the
 * "action_handlers" registry (the same mechanism web_ir_actions_act_multi uses).
 *
 * @param {Object} env the Odoo environment
 * @returns {Promise<void>}
 */
async function executeReloadAction({ env }) {
    const actionService = env.services.action;
    const controller = actionService.currentController;
    if (!controller) {
        return;
    }
    const action = controller.action;
    if (!action || !action.type) {
        return;
    }
    // Re-run the current action. For act_window actions doAction reloads the
    // current record; other actions are re-executed the same way.
    await actionService.doAction(
        action.type === "ir.actions.act_window"
            ? { ...action, res_id: action.res_id }
            : action
    );
}

registry
    .category("action_handlers")
    .add("ir.actions.act_view_reload", executeReloadAction);
