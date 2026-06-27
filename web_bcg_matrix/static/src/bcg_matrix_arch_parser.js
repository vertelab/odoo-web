import { visitXML } from "@web/core/utils/xml";

export class BcgMatrixArchParser {
    parse(arch) {
        const archInfo = { fieldNames: [] };
        visitXML(arch, (node) => {
            if (node.tagName === "bcg_matrix") {
                archInfo.xField = node.getAttribute("x_field") || "x_value";
                archInfo.yField = node.getAttribute("y_field") || "y_value";
                archInfo.xLabel = node.getAttribute("x_label") || "X Axis";
                archInfo.yLabel = node.getAttribute("y_label") || "Y Axis";
                archInfo.labelField = node.getAttribute("label_field") || "display_name";
                archInfo.sizeField = node.getAttribute("size_field") || null;
                archInfo.colorField = node.getAttribute("color_field") || null;
                archInfo.xMidpoint = parseFloat(node.getAttribute("x_midpoint") || "0");
                archInfo.yMidpoint = parseFloat(node.getAttribute("y_midpoint") || "0");
                archInfo.title = node.getAttribute("string") || "BCG Matrix";
                archInfo.quadrantLabels = (node.getAttribute("quadrant_labels") || "Stars,Cash Cows,Question Marks,Dogs").split(",");
                archInfo.fieldNames.push(archInfo.xField, archInfo.yField, archInfo.labelField);
                if (archInfo.sizeField) archInfo.fieldNames.push(archInfo.sizeField);
                if (archInfo.colorField) archInfo.fieldNames.push(archInfo.colorField);
            }
        });
        archInfo.fieldNames = [...new Set(archInfo.fieldNames)];
        return archInfo;
    }
}
