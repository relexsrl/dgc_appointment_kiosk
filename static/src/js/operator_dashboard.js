/** @odoo-module **/

import {Component, useState, onWillStart, onMounted, onWillUnmount} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {_t} from "@web/core/l10n/translation";

export class DgcOperatorDashboard extends Component {
    static template = "dgc_appointment_kiosk.OperatorDashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.busService = useService("bus_service");

        this.state = useState({
            currentTurn: null,
            waitingTurns: [],
            doneTurns: [],
            loading: true,
            timerDisplay: "--:--:--",
        });
        this.timerInterval = null;

        onWillStart(async () => {
            await this.loadData();
        });
        onMounted(() => {
            this._startTimer();
            this.busService.subscribe("dgc_turn_update", () => this.loadData());
        });
        onWillUnmount(() => {
            this._stopTimer();
        });
    }

    async loadData() {
        try {
            const data = await this.orm.call(
                "dgc.appointment.turn",
                "get_operator_dashboard_data",
                [],
            );
            this.state.currentTurn = data.current_turn || null;
            this.state.waitingTurns = data.waiting_turns || [];
            this.state.doneTurns = data.done_turns || [];
            this.state.loading = false;
        } catch {
            this.state.loading = false;
        }
    }

    // --- Timer ---

    _startTimer() {
        this._tickTimer();
        this.timerInterval = setInterval(() => this._tickTimer(), 1000);
    }

    _stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }

    _tickTimer() {
        const turn = this.state.currentTurn;
        if (!turn || turn.state !== "serving" || !turn.serve_date) {
            this.state.timerDisplay = "--:--:--";
            return;
        }
        const serveDate = luxon.DateTime.fromSQL(turn.serve_date, {zone: "utc"}).toLocal();
        const now = luxon.DateTime.now();
        const diff = now.diff(serveDate, ["hours", "minutes", "seconds"]);
        const h = String(Math.floor(Math.abs(diff.hours))).padStart(2, "0");
        const m = String(Math.floor(Math.abs(diff.minutes))).padStart(2, "0");
        const s = String(Math.floor(Math.abs(diff.seconds))).padStart(2, "0");
        this.state.timerDisplay = `${h}:${m}:${s}`;
    }

    // --- Actions ---

    async callNext() {
        if (!this.state.waitingTurns.length) return;
        const turnId = this.state.waitingTurns[0].id;
        try {
            await this.orm.call("dgc.appointment.turn", "action_call", [turnId]);
            await this.loadData();
        } catch (e) {
            this.notification.add(_t("No se pudo llamar el turno. Intente nuevamente."), {
                type: "danger",
            });
            await this.loadData();
        }
    }

    async callTurn(turnId) {
        try {
            await this.orm.call("dgc.appointment.turn", "action_call", [turnId]);
            await this.loadData();
        } catch {
            this.notification.add(_t("Error al llamar el turno."), {type: "danger"});
            await this.loadData();
        }
    }

    async recallTurn() {
        if (!this.state.currentTurn) return;
        try {
            await this.orm.call("dgc.appointment.turn", "action_recall", [this.state.currentTurn.id]);
            await this.loadData();
        } catch {
            this.notification.add(_t("Error al re-llamar."), {type: "danger"});
        }
    }

    async serveTurn() {
        if (!this.state.currentTurn) return;
        try {
            await this.orm.call("dgc.appointment.turn", "action_serve", [this.state.currentTurn.id]);
            await this.loadData();
        } catch {
            this.notification.add(_t("Error al iniciar atención."), {type: "danger"});
        }
    }

    async finalizeTurn() {
        if (!this.state.currentTurn) return;
        try {
            await this.orm.call("dgc.appointment.turn", "action_done", [this.state.currentTurn.id]);
            this.notification.add(_t("Turno finalizado."), {type: "success"});
            await this.loadData();
        } catch {
            this.notification.add(_t("Error al finalizar."), {type: "danger"});
        }
    }

    async noShowTurn() {
        if (!this.state.currentTurn) return;
        try {
            await this.orm.call("dgc.appointment.turn", "action_no_show", [this.state.currentTurn.id]);
            this.notification.add(_t("Turno marcado como no presentado."), {type: "warning"});
            await this.loadData();
        } catch {
            this.notification.add(_t("Error al marcar no presentado."), {type: "danger"});
        }
    }

    async deriveTurn() {
        if (!this.state.currentTurn) return;
        this.action.doAction(
            {
                type: "ir.actions.act_window",
                name: _t("Derivar Turno"),
                res_model: "dgc.turn.derive.wizard",
                views: [[false, "form"]],
                target: "new",
                context: {default_turn_id: this.state.currentTurn.id},
            },
            {onClose: () => this.loadData()},
        );
    }

    openTurnForm(turnId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "dgc.appointment.turn",
            res_id: turnId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    openCreateWizard() {
        this.action.doAction(
            {
                type: "ir.actions.act_window",
                name: _t("Crear Turno Manual"),
                res_model: "dgc.turn.create.wizard",
                views: [[false, "form"]],
                target: "new",
            },
            {onClose: () => this.loadData()},
        );
    }

    formatDuration(minutes) {
        if (!minutes) return "00:00";
        const m = Math.floor(minutes);
        const s = Math.round((minutes - m) * 60);
        return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
    }
}

registry.category("actions").add("dgc_operator_dashboard", DgcOperatorDashboard);
