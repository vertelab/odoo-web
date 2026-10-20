/** @odoo-module **/

import { registry } from "@web/core/registry";
import { FloatTimeField, floatTimeField } from "@web/views/fields/float_time/float_time_field";
import { Component, useRef, useState, onMounted, onWillUnmount } from "@odoo/owl";

const MINUTE_STEP = 15;
const HOURS = Array.from({ length: 24 }, (_, i) => ({
    value: String(i).padStart(2, "0"),
    label: String(i).padStart(2, "0"),
}));
const MINUTES = Array.from({ length: 60 / MINUTE_STEP }, (_, i) => {
    const v = i * MINUTE_STEP;
    return { value: String(v).padStart(2, "0"), label: String(v).padStart(2, "0") };
});

export class TimepickerPopup extends Component {
    static template = "timepicker_field.TimepickerPopup";
    static props = {
        hour: String,
        minute: String,
        anchorEl: { type: Object, optional: true },
        onApply: Function,
        onClose: Function,
    };

    setup() {
        this.popupRef = useRef("popup");
        this.state = useState({
            hour: this.props.hour,
            minute: this._snapMinute(this.props.minute),
            popupStyle: "display:none;",
        });
        this._onDocClick = this._onDocClick.bind(this);
        onMounted(() => {
            this._positionPopup();
            document.addEventListener("mousedown", this._onDocClick, true);
        });
        onWillUnmount(() => {
            document.removeEventListener("mousedown", this._onDocClick, true);
        });
    }

    get hours() { return HOURS; }
    get minutes() { return MINUTES; }

    _snapMinute(raw) {
        const n = parseInt(raw, 10) || 0;
        const snapped = Math.round(n / MINUTE_STEP) * MINUTE_STEP;
        return String(snapped >= 60 ? 0 : snapped).padStart(2, "0");
    }

    _positionPopup() {
        const el = this.popupRef.el;
        const anchor = this.props.anchorEl;
        if (!el || !anchor) return;
        const rect = anchor.getBoundingClientRect();
        let top = rect.bottom + 4;
        let left = rect.left;
        // Viewport-aware: flip up if no room below
        if (top + 160 > window.innerHeight) {
            top = rect.top - 160;
        }
        // Clamp left
        if (left + 240 > window.innerWidth) {
            left = window.innerWidth - 250;
        }
        if (left < 4) left = 4;
        this.state.popupStyle = `top:${top}px;left:${left}px;display:flex;`;
    }

    adjustHour(offset) {
        let h = (parseInt(this.state.hour, 10) + offset + 24) % 24;
        this.state.hour = String(h).padStart(2, "0");
    }

    adjustMinute(offset) {
        let m = parseInt(this.state.minute, 10) + offset * MINUTE_STEP;
        if (m >= 60) m = 0;
        if (m < 0) m = 60 - MINUTE_STEP;
        this.state.minute = String(m).padStart(2, "0");
    }

    onHourChange(ev) {
        this.state.hour = ev.target.value;
    }

    onMinuteChange(ev) {
        this.state.minute = ev.target.value;
    }

    onApply() {
        this.props.onApply(this.state.hour, this.state.minute);
    }

    onPopupMousedown(ev) {
        // Prevent input blur when clicking inside popup
        ev.preventDefault();
    }

    _onDocClick(ev) {
        const el = this.popupRef.el;
        if (el && !el.contains(ev.target) && !this.props.anchorEl.contains(ev.target)) {
            this.props.onClose();
        }
    }
}

export class TimepickerField extends FloatTimeField {
    static template = "timepicker_field.TimepickerField";
    static components = { ...FloatTimeField.components, TimepickerPopup };
    static props = { ...FloatTimeField.props };

    setup() {
        super.setup();
        this.timeInputRef = useRef("numpadDecimal");
        this.state = useState({ showPopup: false });
    }

    _parseCurrentTime() {
        const el = this.timeInputRef.el;
        if (el && el.value) {
            const parts = el.value.split(":");
            return {
                hour: (parts[0] || "00").padStart(2, "0"),
                minute: (parts[1] || "00").padStart(2, "0"),
            };
        }
        return { hour: "00", minute: "00" };
    }

    onInputClick() {
        if (this.props.readonly) return;
        this.state.showPopup = !this.state.showPopup;
    }

    onTimepickerApply(hour, minute) {
        const h = parseInt(hour, 10);
        const m = parseInt(minute, 10);
        const floatValue = h + m / 60;
        this.props.record.update({ [this.props.name]: floatValue });
        this.state.showPopup = false;
    }

    onTimepickerClose() {
        this.state.showPopup = false;
    }

    get popupProps() {
        const { hour, minute } = this._parseCurrentTime();
        return {
            hour,
            minute,
            anchorEl: this.timeInputRef.el,
            onApply: this.onTimepickerApply.bind(this),
            onClose: this.onTimepickerClose.bind(this),
        };
    }
}

export const timepickerField = {
    ...floatTimeField,
    component: TimepickerField,
};

registry.category("fields").add("timepicker_field", timepickerField);
