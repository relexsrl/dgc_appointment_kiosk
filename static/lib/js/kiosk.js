/**
 * DGC Kiosk - Touchscreen Turn Management
 * Vanilla JS (no OWL) - runs on public pages without Odoo web client
 */
class DgcKiosk {
    constructor() {
        this.container = document.querySelector(".kiosk-container");
        this.currentStep = 1;
        this.dniInput = document.getElementById("dni-input");
        this.timeout = parseInt(this.container?.dataset.timeout || "30", 10);
        this.requireEmail = this.container?.dataset.requireEmail === "True";
        this.countdownInterval = null;
        this.areaCache = null;
        this.areaCacheTime = 0;
        this.CACHE_TTL = 5 * 60 * 1000; // 5 minutes

        this._bindEvents();
    }

    _bindEvents() {
        // Numpad event delegation
        const numpad = document.querySelector(".numpad");
        if (numpad) {
            numpad.addEventListener("click", (e) => {
                const btn = e.target.closest(".numpad-btn");
                if (!btn) return;
                const value = btn.dataset.value;
                if (value === "clear") {
                    this.dniInput.value = "";
                } else if (value === "next") {
                    this._onNextStep1();
                } else {
                    if (this.dniInput.value.length < 11) {
                        this.dniInput.value += value;
                    }
                }
            });
        }

        // Back buttons
        const btnBack1 = document.getElementById("btn-back-1");
        if (btnBack1) {
            btnBack1.addEventListener("click", () => this.showStep(1));
        }

        // Retry button
        const btnRetry = document.getElementById("btn-retry");
        if (btnRetry) {
            btnRetry.addEventListener("click", () => this.showStep(1));
        }

        // Area list delegation
        const areaList = document.getElementById("area-list");
        if (areaList) {
            areaList.addEventListener("click", (e) => {
                const card = e.target.closest(".area-card");
                if (!card) return;
                const areaId = card.dataset.areaId;
                this._onAreaSelected(areaId);
            });
        }
    }

    showStep(step) {
        document.querySelectorAll(".step").forEach((el) => el.classList.remove("active"));
        const target = document.getElementById(`step-${step}`);
        if (target) {
            target.classList.add("active");
        }
        this.currentStep = step;

        if (step === 1) {
            this.dniInput.value = "";
            this._hideError("dni-error");
            this._hideError("area-error");
            this._clearCountdown();
        }
    }

    _showError(elementId, message) {
        const el = document.getElementById(elementId);
        if (el) {
            el.textContent = message;
            el.style.display = "block";
        }
    }

    _hideError(elementId) {
        const el = document.getElementById(elementId);
        if (el) {
            el.style.display = "none";
        }
    }

    validateDni(value) {
        if (!value || !/^\d+$/.test(value)) return false;
        const len = value.length;
        return len === 7 || len === 8 || len === 11;
    }

    async _onNextStep1() {
        const dni = this.dniInput.value.trim();
        this._hideError("dni-error");

        if (!this.validateDni(dni)) {
            this._showError("dni-error", "Ingrese un DNI (7-8 dígitos) o CUIT (11 dígitos) válido.");
            return;
        }

        const ok = await this.fetchAreas();
        if (ok) this.showStep(2);
    }

    async fetchAreas() {
        const now = Date.now();
        if (this.areaCache && now - this.areaCacheTime < this.CACHE_TTL) {
            this._renderAreas(this.areaCache);
            return true;
        }

        try {
            const result = await this._jsonRpc("/kiosk/api/areas");
            this.areaCache = result;
            this.areaCacheTime = now;
            this._renderAreas(result);
            return true;
        } catch {
            this._showError("area-error", "Error al cargar las áreas. Intente nuevamente.");
            return false;
        }
    }

    _renderAreas(areas) {
        const list = document.getElementById("area-list");
        list.innerHTML = "";

        for (const area of areas) {
            const card = document.createElement("div");
            card.className = "area-card";
            card.dataset.areaId = area.id;

            const remaining = area.remaining_turns_today;
            const total = area.max_daily_turns;
            const pct = total > 0 ? Math.round((remaining / total) * 100) : 0;
            const full = remaining <= 0;

            card.innerHTML = `
                <div class="area-info">
                    <div class="area-name">${this._escapeHtml(area.name)}</div>
                    <div class="area-location">${this._escapeHtml(area.location)}</div>
                </div>
                <div class="area-capacity">
                    <div class="capacity-bar">
                        <div class="capacity-fill ${full ? 'full' : ''}"
                             style="width: ${pct}%"></div>
                    </div>
                    <div class="capacity-text">${remaining} turnos disponibles</div>
                </div>
            `;

            if (full) {
                card.classList.add("area-full");
            }

            list.appendChild(card);
        }
    }

    async _onAreaSelected(areaId) {
        const dni = this.dniInput.value.trim();
        this._hideError("area-error");

        const card = document.querySelector(`.area-card[data-area-id="${areaId}"]`);
        if (card && card.classList.contains("area-full")) {
            this._showError("area-error", "No hay turnos disponibles para esta área.");
            return;
        }

        try {
            const result = await this.createTurn(dni, areaId);
            if (result.success) {
                document.getElementById("turn-number-display").textContent = result.turn_number;
                document.getElementById("turn-area-display").textContent = result.area_name;
                document.getElementById("turn-location").textContent = result.area_location || "";

                const turnsAhead = result.turns_ahead ?? 0;
                const waitMin = result.estimated_wait_minutes ?? 0;
                document.getElementById("turns-ahead-display").textContent = turnsAhead;
                if (waitMin <= 0) {
                    document.getElementById("estimated-wait-display").textContent = "Próximo en atender";
                } else {
                    document.getElementById("estimated-wait-display").textContent = `~${waitMin} min`;
                }

                this.showStep(3);
                this.startCountdown(this.timeout);
                // Invalidate cache since a turn was taken
                this.areaCache = null;
            } else {
                this._showError("area-error", result.message || "Error al crear el turno.");
            }
        } catch {
            this._showError("area-error", "Error de conexión. Intente nuevamente.");
        }
    }

    async createTurn(dni, areaId, email, notes) {
        return this._jsonRpc("/kiosk/api/turn/create", {
            dni: dni,
            area_id: areaId,
            email: email || null,
            notes: notes || null,
        });
    }

    startCountdown(seconds) {
        this._clearCountdown();
        let remaining = seconds;
        const el = document.getElementById("countdown");

        const tick = () => {
            if (remaining <= 0) {
                this._clearCountdown();
                this.showStep(1);
                return;
            }
            if (el) el.textContent = remaining;
            remaining--;
        };

        tick();
        this.countdownInterval = setInterval(tick, 1000);
    }

    _clearCountdown() {
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
            this.countdownInterval = null;
        }
    }

    async _jsonRpc(url, params) {
        const response = await fetch(url, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                jsonrpc: "2.0",
                method: "call",
                params: params || {},
            }),
        });
        const data = await response.json();
        if (data.error) {
            throw new Error(data.error.message || "Error del servidor");
        }
        return data.result;
    }

    _escapeHtml(str) {
        if (!str) return "";
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    new DgcKiosk();
});
