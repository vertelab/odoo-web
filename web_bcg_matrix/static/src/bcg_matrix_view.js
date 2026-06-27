import { registry } from "@web/core/registry";
import { Model } from "@web/model/model";
import { BcgMatrixArchParser } from "./bcg_matrix_arch_parser";
import { BcgMatrixController } from "./bcg_matrix_controller";
import { BcgMatrixRenderer } from "./bcg_matrix_renderer";

export const bcgMatrixView = {
    type: "bcg_matrix",

    Controller: BcgMatrixController,
    Renderer: BcgMatrixRenderer,
    Model: Model,
    ArchParser: BcgMatrixArchParser,

    buttonTemplate: "web_bcg_matrix.BcgMatrixView.Buttons",

    props: (genericProps, view) => {
        const { arch, fields, resModel } = genericProps;
        const archInfo = new view.ArchParser().parse(arch);
        return {
            ...genericProps,
            Model: view.Model,
            Renderer: view.Renderer,
            buttonTemplate: view.buttonTemplate,
            archInfo,
            modelParams: { resModel, fields, archInfo },
        };
    },
};

registry.category("views").add("bcg_matrix", bcgMatrixView);
