/** @odoo-module **/

import {Component, useState, onWillStart, onMounted, onWillUnmount} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {_t} from "@web/core/l10n/translation";

const BUS_HEARTBEAT_TIMEOUT = 60000; // 60 seconds
const DEBOUNCE_RELOAD_MS = 300; // 300ms trailing-edge debounce

export class DgcAdminDashboard extends Component {
    static template = "dgc_appointment_kiosk.AdminDashboard";

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.busState = useService("dgc_turn_bus");

        this.state = useState({
            loading: true,
            globalSummary: {
                total_waiting: 0,
                total_serving: 0,
                total_done: 0,
                total_no_show: 0,
                total_derived: 0,
                total_remaining: 0,
                avg_duration: 0,
                avg_wait_time: 0,
            },
            areas: [],
            busConnected: false,
        });

        this._reloadTimeout = null;
        this._busHeartbeatTimer = null;

        this._onDgcTurnUpdate = () => {
            this._markBusAlive();
            this._debouncedReload();
        };

        this._onDgcBusConnected = () => {
            this._markBusAlive();
        };

        onWillStart(async () => {
            await this.loadData();
        });

        onMounted(() => {
            document.addEventListener("dgc_turn_update", this._onDgcTurnUpdate);
            document.addEventListener("dgc_bus_connected", this._onDgcBusConnected);
            // Check if bus service already connected (race condition guard)
            if (this.busState?.connected) {
                this._markBusAlive();
            }
        });

        onWillUnmount(() => {
            document.removeEventListener("dgc_turn_update", this._onDgcTurnUpdate);
            document.removeEventListener("dgc_bus_connected", this._onDgcBusConnected);
            if (this._reloadTimeout) {
                clearTimeout(this._reloadTimeout);
                this._reloadTimeout = null;
            }
            this._stopBusHeartbeat();
        });
    }

    // --- Data Loading ---

    async loadData() {
        try {
            const data = await this.orm.call(
                "dgc.appointment.turn",
                "get_admin_dashboard_data",
                [],
            );
            this.state.areas = data.areas || [];
            Object.assign(this.state.globalSummary, data.global_summary || {});
            this.state.loading = false;
        } catch {
            this.state.loading = false;
            this.notification.add(_t("Error al cargar datos del panel."), {type: "danger"});
        }
    }

    // --- Debounced Reload (300ms trailing edge) ---

    _debouncedReload() {
        if (this._reloadTimeout) {
            clearTimeout(this._reloadTimeout);
        }
        this._reloadTimeout = setTimeout(() => {
            this.loadData();
        }, DEBOUNCE_RELOAD_MS);
    }

    // --- Bus Heartbeat ---

    _stopBusHeartbeat() {
        if (this._busHeartbeatTimer) {
            clearTimeout(this._busHeartbeatTimer);
            this._busHeartbeatTimer = null;
        }
    }

    _markBusAlive() {
        this.state.busConnected = true;
        this._stopBusHeartbeat();
        this._busHeartbeatTimer = setTimeout(() => {
            this.state.busConnected = false;
        }, BUS_HEARTBEAT_TIMEOUT);
    }

    // --- Template Helper Methods ---

    /**
     * Return sorted areas: those with waiting turns first (descending),
     * then alphabetically by name.
     */
    get sortedAreas() {
        return [...this.state.areas].sort((a, b) => {
            if (b.waiting_count !== a.waiting_count) {
                return b.waiting_count - a.waiting_count;
            }
            return (a.name || "").localeCompare(b.name || "");
        });
    }

    formatDuration(minutes) {
        if (!minutes) return "0m";
        return minutes < 60
            ? `${Math.round(minutes)}m`
            : `${Math.floor(minutes / 60)}h ${Math.round(minutes % 60)}m`;
    }

    getStatusLabel(status) {
        const labels = {
            serving: _t("Atendiendo"),
            calling: _t("Llamando"),
            idle: _t("Disponible"),
            offline: _t("Cerrado"),
        };
        return labels[status] || status;
    }

    getStatusClass(status) {
        const classes = {
            serving: "dgc-admin-status-badge--serving",
            calling: "dgc-admin-status-badge--calling",
            idle: "dgc-admin-status-badge--idle",
            offline: "dgc-admin-status-badge--offline",
        };
        return classes[status] || "";
    }

    getCapacityPercent(area) {
        if (!area.max_daily_turns) return 0;
        const used = area.max_daily_turns - (area.remaining_turns || 0);
        return Math.min(Math.round((used / area.max_daily_turns) * 100), 100);
    }

    getCapacityClass(area) {
        const pct = this.getCapacityPercent(area);
        if (pct > 85) return "dgc-admin-capacity-bar__fill--danger";
        if (pct > 60) return "dgc-admin-capacity-bar__fill--warning";
        return "";
    }
}

registry.category("actions").add("dgc_admin_dashboard", DgcAdminDashboard);
