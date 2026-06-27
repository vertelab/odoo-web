import { visitXML } from "@web/core/utils/xml";

export class YearWheelArchParser {
    parse(arch) {
        const archInfo = {
            fieldNames: [],
        };
        visitXML(arch, (node) => {
            if (node.tagName === "year_wheel") {
                archInfo.dateField = node.getAttribute("date_field") || "date";
                archInfo.colorField = node.getAttribute("color_field") || "state";
                archInfo.labelField = node.getAttribute("label_field") || "display_name";
                archInfo.sizeField = node.getAttribute("size_field") || null;
                archInfo.startMonth = parseInt(node.getAttribute("start_month") || "1", 10);
                archInfo.segments = parseInt(node.getAttribute("segments") || "12", 10);
                archInfo.title = node.getAttribute("string") || "Year Wheel";
                archInfo.fieldNames.push(archInfo.dateField, archInfo.colorField, archInfo.labelField);
                if (archInfo.sizeField) archInfo.fieldNames.push(archInfo.sizeField);
            }
        });
        archInfo.fieldNames = [...new Set(archInfo.fieldNames)];
        return archInfo;
    }
}
