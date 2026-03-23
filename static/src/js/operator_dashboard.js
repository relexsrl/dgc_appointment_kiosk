/** @odoo-module **/

import {Component, useState, onWillStart, onMounted, onWillUnmount} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {_t} from "@web/core/l10n/translation";

const BUS_HEARTBEAT_TIMEOUT = 60000; // 60 seconds
const NEW_TURN_ANIMATION_MS = 3000; // 3 seconds

export class DgcOperatorDashboard extends Component {
    static template = "dgc_appointment_kiosk.OperatorDashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        this.state = useState({
            currentTurn: null,
            waitingTurns: [],
            doneTurns: [],
            loading: true,
            timerDisplay: "--:--:--",
            // KPI state
            kpis: {
                served_count: 0,
                avg_duration: 0,
                pending_count: 0,
                derivation_count: 0,
            },
            // Bus connectivity
            busConnected: false,
            // Done section collapsed by default
            doneExpanded: false,
        });

        this.timerInterval = null;
        this._busHeartbeatTimer = null;
        this._previousWaitingIds = new Set();
        this._newTurnTimers = [];

        this._onDgcTurnUpdate = () => {
            this._markBusAlive();
            this.loadData();
        };

        onWillStart(async () => {
            await this.loadData();
        });
        onMounted(() => {
            this._startTimer();
            document.addEventListener("dgc_turn_update", this._onDgcTurnUpdate);
            // Initialize bus heartbeat — assume connected if event arrives within timeout
            this._startBusHeartbeat();
        });
        onWillUnmount(() => {
            this._stopTimer();
            this._stopBusHeartbeat();
            this._clearNewTurnTimers();
            document.removeEventListener("dgc_turn_update", this._onDgcTurnUpdate);
        });
    }

    async loadData() {
        try {
            const data = await this.orm.call(
                "dgc.appointment.turn",
                "get_operator_dashboard_data",
                [],
            );

            // Detect new turns in the waiting queue for animation
            const oldIds = this._previousWaitingIds;
            const newWaiting = data.waiting_turns || [];
            const newIds = new Set(newWaiting.map((t) => t.id));

            // Mark newly appeared turns
            for (const turn of newWaiting) {
                if (!oldIds.has(turn.id)) {
                    turn.__is_new = true;
                    // Schedule removal of the animation flag
                    const timer = setTimeout(() => {
                        turn.__is_new = false;
                    }, NEW_TURN_ANIMATION_MS);
                    this._newTurnTimers.push(timer);
                }
            }
            this._previousWaitingIds = newIds;

            this.state.currentTurn = data.current_turn || null;
            this.state.waitingTurns = newWaiting;
            this.state.doneTurns = data.done_turns || [];
            this.state.loading = false;

            // Assign KPIs from backend
            if (data.kpis) {
                this.state.kpis.served_count = data.kpis.served_count || 0;
                this.state.kpis.avg_duration = data.kpis.avg_duration || 0;
                this.state.kpis.pending_count = data.kpis.pending_count || 0;
                this.state.kpis.derivation_count = data.kpis.derivation_count || 0;
            }
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

    // --- Bus Heartbeat ---

    _startBusHeartbeat() {
        // Will be set to connected when first bus event arrives
        this.state.busConnected = false;
    }

    _stopBusHeartbeat() {
        if (this._busHeartbeatTimer) {
            clearTimeout(this._busHeartbeatTimer);
            this._busHeartbeatTimer = null;
        }
    }

    _markBusAlive() {
        this.state.busConnected = true;
        // Reset the heartbeat timeout
        this._stopBusHeartbeat();
        this._busHeartbeatTimer = setTimeout(() => {
            this.state.busConnected = false;
        }, BUS_HEARTBEAT_TIMEOUT);
    }

    // --- New Turn Animation Cleanup ---

    _clearNewTurnTimers() {
        for (const timer of this._newTurnTimers) {
            clearTimeout(timer);
        }
        this._newTurnTimers = [];
    }

    // --- Toggle Done Section ---

    toggleDoneSection() {
        this.state.doneExpanded = !this.state.doneExpanded;
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
            this.notification.add(_t("Error al iniciar atencion."), {type: "danger"});
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
                context: {
                    default_turn_id: this.state.currentTurn.id,
                    dialog_size: "medium",
                },
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
        if (!minutes) return "0m";
        return minutes < 60
            ? `${Math.round(minutes)}m`
            : `${Math.floor(minutes / 60)}h ${Math.round(minutes % 60)}m`;
    }
}

registry.category("actions").add("dgc_operator_dashboard", DgcOperatorDashboard);
