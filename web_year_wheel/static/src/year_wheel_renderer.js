import { Component, useEffect, useRef } from "@odoo/owl";

const MONTHS = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
];

const COLORS = [
    "#4e79a7", "#f28e2b", "#e15759", "#76b7b2",
    "#59a14f", "#edc948", "#b07aa1", "#ff9da7",
    "#9c755f", "#bab0ac"
];

export class YearWheelRenderer extends Component {
    static template = "web_year_wheel.YearWheelRenderer";
    static props = {
        model: Object,
        archInfo: Object,
    };

    setup() {
        this.svgRef = useRef("svg");
        useEffect(() => this._drawWheel());
    }

    _drawWheel() {
        // SVG-based circular year wheel with segments
        // This is a placeholder that will be filled by the actual rendering
        // Data will come from this.props.model after load()
    }

    _getSegmentPath(cx, cy, r, startAngle, endAngle) {
        const startRad = ((startAngle - 90) * Math.PI) / 180;
        const endRad = ((endAngle - 90) * Math.PI) / 180;
        const x1 = cx + r * Math.cos(startRad);
        const y1 = cy + r * Math.sin(startRad);
        const x2 = cx + r * Math.cos(endRad);
        const y2 = cy + r * Math.sin(endRad);
        const largeArc = endAngle - startAngle > 180 ? 1 : 0;
        return `M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2} Z`;
    }

    get segments() {
        return this.props.archInfo.segments || 12;
    }
    get title() {
        return this.props.archInfo.title || "Year Wheel";
    }
}
