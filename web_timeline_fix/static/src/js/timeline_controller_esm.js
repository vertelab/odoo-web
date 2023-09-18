/** @odoo-module **/

import AbstractController from "@web_timeline/js/timeline_controller.esm";
import {FormViewDialog} from "@web/views/view_dialogs/form_view_dialog";
import core from "web.core";
import Dialog from "web.Dialog";
var _t = core._t;
import {Component} from "@odoo/owl";

export default AbstractController.include({
    _onAdd: function (event) {
        const item = event.data.item;
        // Initialize default values for creation
        const default_context = {};
        default_context["default_".concat(this.date_start)] = item.start;
        if (this.date_delay) {
            default_context["default_".concat(this.date_delay)] = 1;
        }
        if (this.date_start) {
            default_context["default_".concat(this.date_start)] = moment(item.start)
                .utc()
                .format("YYYY-MM-DD HH:mm:ss");
        }
        if (this.date_stop && item.end) {
            default_context["default_".concat(this.date_stop)] = moment(item.end)
                .utc()
                .format("YYYY-MM-DD HH:mm:ss");
        }
        if (this.date_delay && this.date_start && this.date_stop && item.end) {
            default_context["default_".concat(this.date_delay)] =
                (moment(item.end) - moment(item.start)) / 3600000;
        }
        if (item.group > 0) {
            default_context["default_".concat(this.renderer.last_group_bys[0])] =
                item.group;
        }
        // Show popup
        this.Dialog = Component.env.services.dialog.add(
            FormViewDialog,
            {
                resId: false,
                context: _.extend(default_context, this.context),
                onRecordSaved: (record) => this.create_completed([record.resId]),
                resModel: this.model.modelName,
            },
            {onClose: () => event.data.callback()}
        );
        return false;
    },

})