/** @odoo-module **/

import {Component, useState, onMounted, onWillUnmount} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";

export class DgcElapsedTimer extends Component {
    static template = "dgc_appointment_kiosk.ElapsedTimer";
    static props = {...standardFieldProps};

    setup() {
        this.state = useState({display: "--:--:--"});
        this.intervalId = null;
        onMounted(() => this._startTimer());
        onWillUnmount(() => this._stopTimer());
    }

    _startTimer() {
        this._tick();
        this.intervalId = setInterval(() => this._tick(), 1000);
    }

    _stopTimer() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }

    _tick() {
        const record = this.props.record;
        const state = record.data.state;
        const serveDate = record.data.serve_date;
        if (state !== "serving" || !serveDate) {
            this.state.display = "--:--:--";
            return;
        }
        // serveDate is a luxon DateTime in Odoo 19
        const now = luxon.DateTime.now();
        const diff = now.diff(serveDate, ["hours", "minutes", "seconds"]);
        const h = String(Math.floor(Math.abs(diff.hours))).padStart(2, "0");
        const m = String(Math.floor(Math.abs(diff.minutes))).padStart(2, "0");
        const s = String(Math.floor(Math.abs(diff.seconds))).padStart(2, "0");
        this.state.display = `${h}:${m}:${s}`;
    }
}

export const dgcElapsedTimer = {
    component: DgcElapsedTimer,
    supportedTypes: ["char"],
};

registry.category("fields").add("dgc_elapsed_timer", dgcElapsedTimer);
