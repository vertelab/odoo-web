import { Component, useRef } from "@odoo/owl";
import { Record } from "@web/model/record";
import { Field } from "@web/views/fields/field";
import { ViewButton } from "@web/views/view_button/view_button";
import { useViewButtons } from "@web/views/view_button/view_button_hook";
import { useViewCompiler } from "@web/views/view_compiler";
import { GanttCompiler } from "./gantt_compiler";

export class GanttPopover extends Component {
    static template = "web_gantt_ce.GanttPopover";
    static components = { Field, ViewButton, Record };
    static props = [
        "title?",
        "displayGenericButtons",
        "bodyTemplate?",
        "footerTemplate?",
        "KanbanRecord?",
        "kanbanViewParams?",
        "resModel",
        "resId",
        "context",
        "close",
        "reloadOnClose",
        "buttons",
        "actionContext?",
    ];

    setup() {
        this.rootRef = useRef("root");

        this.templates = {};
        const toCompile = {};
        const { bodyTemplate, footerTemplate } = this.props;
        if (bodyTemplate) {
            toCompile.body = bodyTemplate;
        }
        if (footerTemplate) {
            toCompile.footer = footerTemplate;
        }
        Object.assign(
            this.templates,
            useViewCompiler(GanttCompiler, toCompile, { recordExpr: "__record__" })
        );

        useViewButtons(this.rootRef, {
            reload: () => {
                this.props.reloadOnClose();
                this.props.close();
            },
        });

        this.displayPopoverHeader = Boolean(this.templates.body);
        if (!this.templates.body) {
            const { kanbanViewParams, resId, resModel } = this.props;
            const { activeFields, archInfo, fields } = kanbanViewParams;
            // Odoo 18's Record takes flat props (resModel, resId, fields,
            // activeFields, mode, values); the previous `hooks`/`context`
            // keys are no longer accepted and make the component throw.
            this.recordProps = {
                resModel,
                resId,
                fields,
                activeFields,
                mode: "readonly",
            };
            this.kanbanViewParams = kanbanViewParams;
            this.archInfo = archInfo;
            this.fields = fields;
        }
    }

    get renderingContext() {
        return Object.assign({}, this.props.context, {
            __comp__: this,
            __record__: { resModel: this.props.resModel, resId: this.props.resId },
        });
    }

    async onClick(button) {
        await button.onClick();
        this.props.close();
    }
}
