/**
 * DGC Kiosk - Touchscreen Turn Management
 * Vanilla JS (no OWL) - runs on public pages without Odoo web client
 */
class DgcKiosk {
    constructor() {
        this.container = document.querySelector(".kiosk-container");
        this.currentStep = 0;
        this.dniInput = document.getElementById("dni-input");
        this.checkDniInput = document.getElementById("check-dni-input");
        this.timeout = parseInt(this.container?.dataset.timeout || "30", 10);
        this.requireEmail = this.container?.dataset.requireEmail === "True";
        this.countdownInterval = null;
        this.areaCache = null;
        this.areaCacheTime = 0;
        this.CACHE_TTL = 5 * 60 * 1000; // 5 minutes

        this._bindEvents();
        this._bindKeyboard();
    }

    _bindEvents() {
        // Step 0 buttons
        const btnNewTurn = document.getElementById("btn-new-turn");
        if (btnNewTurn) {
            btnNewTurn.addEventListener("click", () => this.showStep(1));
        }
        const btnCheckTurn = document.getElementById("btn-check-turn");
        if (btnCheckTurn) {
            btnCheckTurn.addEventListener("click", () => this.showStep("check"));
        }

        // Numpad event delegation (Step 1 - new turn)
        const numpad = document.querySelector("#step-1 .numpad");
        if (numpad) {
            numpad.addEventListener("click", (e) => {
                const btn = e.target.closest(".numpad-btn");
                if (!btn) return;
                const value = btn.dataset.value;
                if (value === "clear") {
                    this.dniInput.value = "";
                    this._updateDniValidation(this.dniInput, "dni-validation", "numpad-next-1");
                } else if (value === "next") {
                    this._onNextStep1();
                } else {
                    if (this.dniInput.value.length < 11) {
                        this.dniInput.value += value;
                    }
                    this._updateDniValidation(this.dniInput, "dni-validation", "numpad-next-1");
                }
            });
        }

        // Numpad event delegation (Check turn flow)
        const checkNumpad = document.querySelector("#step-check .numpad");
        if (checkNumpad) {
            checkNumpad.addEventListener("click", (e) => {
                const btn = e.target.closest(".numpad-btn");
                if (!btn) return;
                const value = btn.dataset.value;
                if (value === "clear") {
                    this.checkDniInput.value = "";
                    this._updateDniValidation(this.checkDniInput, "check-dni-validation", "numpad-next-check");
                } else if (value === "next") {
                    this._onCheckTurnSubmit();
                } else {
                    if (this.checkDniInput.value.length < 11) {
                        this.checkDniInput.value += value;
                    }
                    this._updateDniValidation(this.checkDniInput, "check-dni-validation", "numpad-next-check");
                }
            });
        }

        // Back buttons
        const btnBack1 = document.getElementById("btn-back-1");
        if (btnBack1) {
            btnBack1.addEventListener("click", () => this.showStep(0));
        }

        const btnBack2 = document.getElementById("btn-back-2");
        if (btnBack2) {
            btnBack2.addEventListener("click", () => this.showStep(1));
        }

        const btnBackCheck = document.getElementById("btn-back-check");
        if (btnBackCheck) {
            btnBackCheck.addEventListener("click", () => this.showStep(0));
        }

        const btnBackCheckResult = document.getElementById("btn-back-check-result");
        if (btnBackCheckResult) {
            btnBackCheckResult.addEventListener("click", () => this.showStep(0));
        }

        // Retry button
        const btnRetry = document.getElementById("btn-retry");
        if (btnRetry) {
            btnRetry.addEventListener("click", () => this.showStep(0));
        }

        // Area list delegation (click + keyboard Enter/Space)
        const areaList = document.getElementById("area-list");
        if (areaList) {
            areaList.addEventListener("click", (e) => {
                const card = e.target.closest(".area-card");
                if (!card) return;
                const areaId = card.dataset.areaId;
                this._onAreaSelected(areaId);
            });
            areaList.addEventListener("keydown", (e) => {
                if (e.key !== "Enter" && e.key !== " ") return;
                const card = e.target.closest(".area-card");
                if (!card) return;
                e.preventDefault();
                const areaId = card.dataset.areaId;
                this._onAreaSelected(areaId);
            });
        }
    }

    _bindKeyboard() {
        document.addEventListener("keydown", (e) => this._onKeyDown(e));
    }

    isOnDniStep() {
        return this.currentStep === 1 || this.currentStep === "check";
    }

    _onKeyDown(e) {
        if (!this.isOnDniStep()) return;

        const inputEl = this.currentStep === 1 ? this.dniInput : this.checkDniInput;
        const validationElId = this.currentStep === 1 ? "dni-validation" : "check-dni-validation";
        const nextBtnId = this.currentStep === 1 ? "numpad-next-1" : "numpad-next-check";

        if (e.key >= "0" && e.key <= "9") {
            e.preventDefault();
            if (inputEl.value.length < 11) {
                inputEl.value += e.key;
            }
            this._updateDniValidation(inputEl, validationElId, nextBtnId);
        } else if (e.key === "Backspace") {
            e.preventDefault();
            inputEl.value = inputEl.value.slice(0, -1);
            this._updateDniValidation(inputEl, validationElId, nextBtnId);
        } else if (e.key === "Delete") {
            e.preventDefault();
            inputEl.value = "";
            this._updateDniValidation(inputEl, validationElId, nextBtnId);
        } else if (e.key === "Enter") {
            e.preventDefault();
            if (this.currentStep === 1) {
                this._onNextStep1();
            } else {
                this._onCheckTurnSubmit();
            }
        }
    }

    showStep(step) {
        document.querySelectorAll(".step").forEach((el) => el.classList.remove("active"));
        const target = document.getElementById(`step-${step}`);
        if (target) {
            target.classList.add("active");
        }
        this.currentStep = step;

        if (step === 0) {
            this.dniInput.value = "";
            if (this.checkDniInput) this.checkDniInput.value = "";
            this._hideError("dni-error");
            this._hideError("area-error");
            this._hideError("check-dni-error");
            this._clearCountdown();
            this._resetDniValidation("dni-validation", "numpad-next-1");
            this._resetDniValidation("check-dni-validation", "numpad-next-check");
            // Reset DNI field visual state
            this.dniInput.classList.remove("valid", "invalid");
            if (this.checkDniInput) this.checkDniInput.classList.remove("valid", "invalid");
        }

        if (step === 1) {
            this.dniInput.value = "";
            this._hideError("dni-error");
            this._hideError("area-error");
            this._clearCountdown();
            this._resetDniValidation("dni-validation", "numpad-next-1");
            this.dniInput.classList.remove("valid", "invalid");
        }

        if (step === "check") {
            if (this.checkDniInput) this.checkDniInput.value = "";
            this._hideError("check-dni-error");
            this._clearCountdown();
            this._resetDniValidation("check-dni-validation", "numpad-next-check");
            if (this.checkDniInput) this.checkDniInput.classList.remove("valid", "invalid");
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

    // --- DNI validation (real-time) ---

    validateDni(value) {
        if (!value || !/^\d+$/.test(value)) return false;
        const len = value.length;
        return len === 7 || len === 8 || len === 11;
    }

    /**
     * Returns validation state for a given DNI string.
     * @returns {{ state: 'neutral'|'valid'|'invalid', message: string }}
     */
    _getDniValidationState(value) {
        if (!value || value.length === 0) {
            return { state: "neutral", message: "" };
        }
        const len = value.length;
        if (len < 7) {
            return { state: "neutral", message: `${len}/8 dígitos` };
        }
        if (len === 7 || len === 8) {
            return { state: "valid", message: `${len === 7 ? "7" : "8"} dígitos — DNI válido ✓` };
        }
        if (len >= 9 && len <= 10) {
            return { state: "invalid", message: "DNI: 7-8 dígitos / CUIT: 11 dígitos" };
        }
        if (len === 11) {
            return { state: "valid", message: "11 dígitos — CUIT válido ✓" };
        }
        // len > 11 should not happen (maxlength=11), but just in case
        return { state: "invalid", message: "Máximo 11 dígitos" };
    }

    _updateDniValidation(inputEl, validationElId, nextBtnId) {
        const value = inputEl.value.trim();
        const { state, message } = this._getDniValidationState(value);
        const valEl = document.getElementById(validationElId);
        if (valEl) {
            valEl.textContent = message;
            valEl.className = `dni-validation ${state}`;
        }
        // Update input field visual state
        inputEl.classList.remove("valid", "invalid");
        if (state === "valid") inputEl.classList.add("valid");
        else if (state === "invalid") inputEl.classList.add("invalid");

        // Enable/disable Next button
        const nextBtn = document.getElementById(nextBtnId);
        if (nextBtn) {
            const isValid = this.validateDni(value);
            if (isValid) {
                nextBtn.classList.remove("numpad-next-disabled");
                nextBtn.removeAttribute("disabled");
            } else {
                nextBtn.classList.add("numpad-next-disabled");
                nextBtn.setAttribute("disabled", "disabled");
            }
        }
    }

    _resetDniValidation(validationElId, nextBtnId) {
        const valEl = document.getElementById(validationElId);
        if (valEl) {
            valEl.textContent = "";
            valEl.className = "dni-validation neutral";
        }
        const nextBtn = document.getElementById(nextBtnId);
        if (nextBtn) {
            nextBtn.classList.add("numpad-next-disabled");
            nextBtn.setAttribute("disabled", "disabled");
        }
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

    // --- Check Turn flow (T-18/T-19) ---

    async _onCheckTurnSubmit() {
        const dni = this.checkDniInput.value.trim();
        this._hideError("check-dni-error");

        if (!this.validateDni(dni)) {
            this._showError("check-dni-error", "Ingrese un DNI (7-8 dígitos) o CUIT (11 dígitos) válido.");
            return;
        }

        try {
            const result = await this._jsonRpc("/kiosk/api/turn/status", { dni: dni });
            this._renderCheckResult(result);
            this.showStep("check-result");
            this.startCountdown(this.timeout, "check-result-countdown", 0);
        } catch {
            this._showError("check-dni-error", "Error de conexión. Intente nuevamente.");
        }
    }

    _renderCheckResult(result) {
        const container = document.getElementById("check-result-content");
        if (!container) return;

        if (result.found) {
            const stateLabels = {
                new: "Nuevo",
                waiting: "En espera",
                calling: "Siendo llamado",
                serving: "En atención",
            };
            const stateLabel = stateLabels[result.state] || result.state;
            const waitText = (result.estimated_wait_minutes != null && result.estimated_wait_minutes > 0)
                ? `~${result.estimated_wait_minutes} min`
                : "Próximo en atender";

            container.innerHTML = `
                <div class="check-result-card">
                    <div class="check-result-icon check-result-found">&#10003;</div>
                    <h2>Turno encontrado</h2>
                    <div class="turn-number-display">${this._escapeHtml(result.turn_number)}</div>
                    <div class="turn-area-display">${this._escapeHtml(result.area_name)}</div>
                    <div class="turn-queue-info">
                        <div class="queue-stat">
                            <span class="queue-label">Estado</span>
                            <span class="queue-value">${this._escapeHtml(stateLabel)}</span>
                        </div>
                        <div class="queue-stat">
                            <span class="queue-label">Posición</span>
                            <span class="queue-value">${result.position ?? "—"}</span>
                        </div>
                        <div class="queue-stat">
                            <span class="queue-label">Espera est.</span>
                            <span class="queue-value">${this._escapeHtml(waitText)}</span>
                        </div>
                    </div>
                </div>
            `;
        } else {
            container.innerHTML = `
                <div class="check-result-card">
                    <div class="check-result-icon check-result-notfound">&#8212;</div>
                    <h2>Sin turno activo</h2>
                    <p class="check-result-message">No se encontró un turno activo para este DNI.</p>
                </div>
            `;
        }
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
            card.setAttribute("tabindex", "0");
            card.setAttribute("role", "button");
            card.setAttribute("aria-label", area.name);

            const remaining = area.remaining_turns_today;
            const total = area.max_daily_turns;
            const pct = total > 0 ? Math.round((remaining / total) * 100) : 0;
            const full = remaining <= 0;

            // T-16: Show description (welcome_message) below area name
            const description = area.welcome_message || "";

            card.innerHTML = `
                <div class="area-info">
                    <div class="area-name">${this._escapeHtml(area.name)}</div>
                    ${description ? `<div class="area-card__description">${this._escapeHtml(description)}</div>` : ""}
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
                this.startCountdown(this.timeout, "countdown", 0);
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

    startCountdown(seconds, countdownElId, resetStep) {
        this._clearCountdown();
        let remaining = seconds;
        const elId = countdownElId || "countdown";
        const resetTo = resetStep !== undefined ? resetStep : 0;
        const el = document.getElementById(elId);

        const tick = () => {
            if (remaining <= 0) {
                this._clearCountdown();
                this.showStep(resetTo);
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

    _bindKeyboard() {
        // Keyboard support for DNI input steps
        document.addEventListener("keydown", (e) => {
            // Only handle numeric keys and backspace
            if (!this.isOnDniStep()) return;

            if (e.key >= "0" && e.key <= "9") {
                // Add digit
                const input = this.currentStep === "check" ? this.checkDniInput : this.dniInput;
                if (input && input.value.length < 11) {
                    input.value += e.key;
                    const valId = this.currentStep === "check" ? "check-dni-validation" : "dni-validation";
                    const btnId = this.currentStep === "check" ? "numpad-next-check" : "numpad-next-1";
                    this._updateDniValidation(input, valId, btnId);
                }
                e.preventDefault();
            } else if (e.key === "Backspace") {
                // Delete last digit
                const input = this.currentStep === "check" ? this.checkDniInput : this.dniInput;
                if (input) {
                    input.value = input.value.slice(0, -1);
                    const valId = this.currentStep === "check" ? "check-dni-validation" : "dni-validation";
                    const btnId = this.currentStep === "check" ? "numpad-next-check" : "numpad-next-1";
                    this._updateDniValidation(input, valId, btnId);
                }
                e.preventDefault();
            } else if (e.key === "Enter") {
                // Submit
                if (this.currentStep === 1) {
                    this._onNextStep1();
                } else if (this.currentStep === "check") {
                    this._onCheckTurnSubmit();
                }
                e.preventDefault();
            }
        });
    }

    isOnDniStep() {
        return this.currentStep === 1 || this.currentStep === "check";
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
