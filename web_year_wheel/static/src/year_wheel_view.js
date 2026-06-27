import { registry } from "@web/core/registry";
import { Model } from "@web/model/model";
import { YearWheelArchParser } from "./year_wheel_arch_parser";
import { YearWheelController } from "./year_wheel_controller";
import { YearWheelRenderer } from "./year_wheel_renderer";

export const yearWheelView = {
    type: "year_wheel",

    Controller: YearWheelController,
    Renderer: YearWheelRenderer,
    Model: Model,
    ArchParser: YearWheelArchParser,

    buttonTemplate: "web_year_wheel.YearWheelView.Buttons",

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

registry.category("views").add("year_wheel", yearWheelView);
