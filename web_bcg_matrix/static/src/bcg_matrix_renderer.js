import { Component } from "@odoo/owl";

const QUADRANT_COLORS = ["#e8f5e9", "#fff3e0", "#e3f2fd", "#fce4ec"]; // green, orange, blue, pink

export class BcgMatrixRenderer extends Component {
    static template = "web_bcg_matrix.BcgMatrixRenderer";
    static props = { model: Object, archInfo: Object };

    get quadrants() { return this.props.archInfo.quadrantLabels || ["Stars","Cash Cows","Question Marks","Dogs"]; }
    get xLabel() { return this.props.archInfo.xLabel; }
    get yLabel() { return this.props.archInfo.yLabel; }
    get title() { return this.props.archInfo.title; }
}
