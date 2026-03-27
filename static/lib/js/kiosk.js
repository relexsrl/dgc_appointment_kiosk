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
        this._isSubmitting = false;

        // Document type: "dni" or "cuit" — separate state per flow
        this.docType = "dni";
        this.checkDocType = "dni";

        this._bindEvents();
        this._bindKeyboard();
        this._bindDocTypeToggles();
    }

    // --- Document type toggle (DNI / CUIT) ---

    _bindDocTypeToggles() {
        // Step 1 toggle
        const toggle1 = document.getElementById("doc-type-toggle-1");
        if (toggle1) {
            toggle1.addEventListener("change", () => {
                this.docType = toggle1.checked ? "cuit" : "dni";
                this._applyDocTypeState(this.dniInput, "dni-validation", "numpad-next-1", "doc-type-switch-1", this.docType);
            });
        }
        // Step Check toggle
        const toggleCheck = document.getElementById("doc-type-toggle-check");
        if (toggleCheck) {
            toggleCheck.addEventListener("change", () => {
                this.checkDocType = toggleCheck.checked ? "cuit" : "dni";
                this._applyDocTypeState(this.checkDniInput, "check-dni-validation", "numpad-next-check", "doc-type-switch-check", this.checkDocType);
            });
        }
    }

    /**
     * Apply doc-type state to input field after toggle change:
     * update maxlength, placeholder, clear input, reset validation, update label highlights.
     */
    _applyDocTypeState(inputEl, validationElId, nextBtnId, switchContainerId, docType) {
        if (!inputEl) return;
        inputEl.value = "";
        inputEl.classList.remove("valid", "invalid");
        if (docType === "cuit") {
            inputEl.setAttribute("maxlength", "13");
            inputEl.setAttribute("placeholder", "XX-XXXXXXXX-X");
        } else {
            inputEl.setAttribute("maxlength", "8");
            inputEl.setAttribute("placeholder", "Ingrese su DNI");
        }
        this._resetDniValidation(validationElId, nextBtnId);

        // Update active label highlight
        const switchEl = document.getElementById(switchContainerId);
        if (switchEl) {
            switchEl.querySelectorAll(".doc-type-label").forEach((lbl) => {
                lbl.classList.toggle("active", lbl.dataset.type === docType);
            });
        }
    }

    /**
     * Auto-format a raw digit string as CUIT: XX-XXXXXXXX-X
     */
    _formatCuit(digits) {
        if (digits.length <= 2) return digits;
        if (digits.length <= 10) return digits.slice(0, 2) + "-" + digits.slice(2);
        return digits.slice(0, 2) + "-" + digits.slice(2, 10) + "-" + digits.slice(10, 11);
    }

    /**
     * Strip non-digit characters from a string.
     */
    _stripNonDigits(value) {
        return value.replace(/\D/g, "");
    }

    /**
     * Return the current doc type for the active step.
     */
    _currentDocType() {
        return this.currentStep === 1 ? this.docType : this.checkDocType;
    }

    /**
     * Extract the kiosk token from the current page URL.
     * URL pattern: /kiosk/<token>/checkin
     */
    _getToken() {
        const parts = window.location.pathname.split('/');
        const kioskIdx = parts.indexOf('kiosk');
        return parts[kioskIdx + 1];
    }

    /**
     * Return the base API path including the kiosk token.
     */
    _getBasePath() {
        return `/kiosk/${this._getToken()}`;
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
                    this._appendDigit(this.dniInput, value, this.docType);
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
                    this._appendDigit(this.checkDniInput, value, this.checkDocType);
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
        const docType = this._currentDocType();

        if (e.key >= "0" && e.key <= "9") {
            e.preventDefault();
            this._appendDigit(inputEl, e.key, docType);
            this._updateDniValidation(inputEl, validationElId, nextBtnId);
        } else if (e.key === "Backspace") {
            e.preventDefault();
            this._removeLastDigit(inputEl, docType);
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

    /**
     * Append a digit to the input, with auto-formatting for CUIT mode.
     */
    _appendDigit(inputEl, digit, docType) {
        if (docType === "cuit") {
            const digits = this._stripNonDigits(inputEl.value);
            if (digits.length >= 11) return;
            const newDigits = digits + digit;
            inputEl.value = this._formatCuit(newDigits);
        } else {
            if (inputEl.value.length < 8) {
                inputEl.value += digit;
            }
        }
    }

    /**
     * Remove the last digit from the input, with re-formatting for CUIT mode.
     */
    _removeLastDigit(inputEl, docType) {
        if (docType === "cuit") {
            const digits = this._stripNonDigits(inputEl.value);
            const newDigits = digits.slice(0, -1);
            inputEl.value = newDigits.length > 0 ? this._formatCuit(newDigits) : "";
        } else {
            inputEl.value = inputEl.value.slice(0, -1);
        }
    }

    showStep(step) {
        document.querySelectorAll(".step").forEach((el) => el.classList.remove("active"));
        const target = document.getElementById(`step-${step}`);
        if (target) {
            target.classList.add("active");
            // Focus management: move focus to heading for screen readers
            const heading = target.querySelector('h2, h1');
            if (heading) {
                heading.setAttribute('tabindex', '-1');
                heading.focus();
            }
        }
        this.currentStep = step;

        if (step === 0) {
            this._isSubmitting = false;
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
            // Reset doc type toggles to DNI
            this._resetDocTypeToggle("doc-type-toggle-1", "doc-type-switch-1", this.dniInput, "dni-validation", "numpad-next-1");
            this.docType = "dni";
            this._resetDocTypeToggle("doc-type-toggle-check", "doc-type-switch-check", this.checkDniInput, "check-dni-validation", "numpad-next-check");
            this.checkDocType = "dni";
        }

        if (step === 1) {
            this.dniInput.value = "";
            this._hideError("dni-error");
            this._hideError("area-error");
            this._clearCountdown();
            this._resetDniValidation("dni-validation", "numpad-next-1");
            this.dniInput.classList.remove("valid", "invalid");
            // Reset doc type toggle to DNI
            this._resetDocTypeToggle("doc-type-toggle-1", "doc-type-switch-1", this.dniInput, "dni-validation", "numpad-next-1");
            this.docType = "dni";
        }

        if (step === "check") {
            if (this.checkDniInput) this.checkDniInput.value = "";
            this._hideError("check-dni-error");
            this._clearCountdown();
            this._resetDniValidation("check-dni-validation", "numpad-next-check");
            if (this.checkDniInput) this.checkDniInput.classList.remove("valid", "invalid");
            // Reset doc type toggle to DNI
            this._resetDocTypeToggle("doc-type-toggle-check", "doc-type-switch-check", this.checkDniInput, "check-dni-validation", "numpad-next-check");
            this.checkDocType = "dni";
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

    validateDni(value, docType) {
        const digits = this._stripNonDigits(value || "");
        if (!digits || !/^\d+$/.test(digits)) return false;
        if (docType === "cuit") {
            return digits.length === 11 && this._validateCuitChecksum(digits);
        }
        // DNI mode
        return digits.length === 7 || digits.length === 8;
    }

    /**
     * Validate CUIT check digit using the modulo 11 algorithm.
     * Matches the backend _validate_cuit() in dgc_appointment_turn.py.
     * @param {string} digits - 11-digit string (no hyphens)
     * @returns {boolean}
     */
    _validateCuitChecksum(digits) {
        if (digits.length !== 11) return false;
        const weights = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2];
        const nums = digits.split("").map(Number);
        let total = 0;
        for (let i = 0; i < 10; i++) {
            total += nums[i] * weights[i];
        }
        const remainder = total % 11;
        let expected;
        if (remainder === 0) expected = 0;
        else if (remainder === 1) expected = 9;
        else expected = 11 - remainder;
        return nums[10] === expected;
    }

    /**
     * Returns validation state for a given input value.
     * @param {string} value - Raw input value (may include hyphens in CUIT mode)
     * @param {string} docType - "dni" or "cuit"
     * @returns {{ state: 'neutral'|'valid'|'invalid', message: string }}
     */
    _getDniValidationState(value, docType) {
        const digits = this._stripNonDigits(value || "");
        if (!digits || digits.length === 0) {
            return { state: "neutral", message: "" };
        }
        const len = digits.length;

        if (docType === "cuit") {
            if (len < 11) {
                return { state: "neutral", message: `${len}/11 dígitos` };
            }
            if (len === 11) {
                if (this._validateCuitChecksum(digits)) {
                    return { state: "valid", message: "CUIT válido ✓" };
                }
                return { state: "invalid", message: "CUIT inválido (dígito verificador)" };
            }
            return { state: "invalid", message: "Máximo 11 dígitos" };
        }

        // DNI mode
        if (len < 7) {
            return { state: "neutral", message: `${len}/8 dígitos` };
        }
        if (len === 7 || len === 8) {
            return { state: "valid", message: `${len} dígitos — DNI válido ✓` };
        }
        return { state: "invalid", message: "DNI: 7-8 dígitos" };
    }

    _updateDniValidation(inputEl, validationElId, nextBtnId) {
        const value = inputEl.value.trim();
        const docType = this._currentDocType();
        const { state, message } = this._getDniValidationState(value, docType);
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
            const isValid = this.validateDni(value, docType);
            if (isValid) {
                nextBtn.classList.remove("numpad-next-disabled");
                nextBtn.removeAttribute("disabled");
            } else {
                nextBtn.classList.add("numpad-next-disabled");
                nextBtn.setAttribute("disabled", "disabled");
            }
        }
    }

    /**
     * Reset a doc-type toggle back to DNI mode.
     */
    _resetDocTypeToggle(toggleId, switchContainerId, inputEl, validationElId, nextBtnId) {
        const toggle = document.getElementById(toggleId);
        if (toggle) toggle.checked = false;
        if (inputEl) {
            inputEl.setAttribute("maxlength", "8");
            inputEl.setAttribute("placeholder", "Ingrese su DNI");
        }
        const switchEl = document.getElementById(switchContainerId);
        if (switchEl) {
            switchEl.querySelectorAll(".doc-type-label").forEach((lbl) => {
                lbl.classList.toggle("active", lbl.dataset.type === "dni");
            });
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
        const raw = this.dniInput.value.trim();
        const dni = this._stripNonDigits(raw);
        this._hideError("dni-error");

        if (!this.validateDni(raw, this.docType)) {
            const msg = this.docType === "cuit"
                ? "Ingrese un CUIT válido (11 dígitos)."
                : "Ingrese un DNI válido (7-8 dígitos).";
            this._showError("dni-error", msg);
            return;
        }

        // Store stripped digits for submission
        this._submittedDni = dni;
        const ok = await this.fetchAreas();
        if (ok) this.showStep(2);
    }

    // --- Check Turn flow (T-18/T-19) ---

    async _onCheckTurnSubmit() {
        if (this._isSubmitting) return;
        const raw = this.checkDniInput.value.trim();
        const dni = this._stripNonDigits(raw);
        this._hideError("check-dni-error");

        if (!this.validateDni(raw, this.checkDocType)) {
            const msg = this.checkDocType === "cuit"
                ? "Ingrese un CUIT válido (11 dígitos)."
                : "Ingrese un DNI válido (7-8 dígitos).";
            this._showError("check-dni-error", msg);
            return;
        }

        this._isSubmitting = true;
        try {
            const result = await this._jsonRpc(`${this._getBasePath()}/api/turn/status`, { dni: dni });
            this._renderCheckResult(result);
            this.showStep("check-result");
            this.startCountdown(this.timeout, "check-result-countdown", 0);
        } catch {
            this._showError("check-dni-error", "Error de conexión. Intente nuevamente.");
        } finally {
            this._isSubmitting = false;
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
                            <span class="queue-value">${this._escapeHtml(String(result.position ?? "—"))}</span>
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
            const result = await this._jsonRpc(`${this._getBasePath()}/api/areas`);
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

            // Estimated wait time display
            const wait = area.estimated_wait_minutes || 0;
            let waitText;
            if (wait <= 0) {
                waitText = "Atenci\u00f3n inmediata";
            } else if (wait < 60) {
                waitText = `~${wait} min de espera`;
            } else {
                const hours = Math.floor(wait / 60);
                const mins = wait % 60;
                waitText = mins > 0 ? `~${hours}h ${mins}min de espera` : `~${hours}h de espera`;
            }

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
                    <div class="area-wait">
                        <span class="wait-icon">\u23F1</span>
                        <span class="wait-text">${this._escapeHtml(waitText)}</span>
                    </div>
                </div>
            `;

            if (full) {
                card.classList.add("area-full");
            }

            // Unavailable area overlay (no active counters or non-working day)
            if (area.available === false) {
                card.classList.add("area-unavailable");
                const overlay = document.createElement("div");
                overlay.className = "area-unavailable-overlay";
                overlay.textContent = "No disponible";
                card.appendChild(overlay);
            }

            list.appendChild(card);
        }
    }

    async _onAreaSelected(areaId) {
        if (this._isSubmitting) return;
        // Use stored stripped digits (set in _onNextStep1)
        const dni = this._submittedDni || this._stripNonDigits(this.dniInput.value.trim());
        this._hideError("area-error");

        const card = document.querySelector(`.area-card[data-area-id="${areaId}"]`);
        if (card && card.classList.contains("area-unavailable")) {
            this._showError("area-error", "El area no se encuentra disponible en este momento.");
            return;
        }
        if (card && card.classList.contains("area-full")) {
            this._showError("area-error", "No hay turnos disponibles para esta area.");
            return;
        }

        this._isSubmitting = true;
        const areaList = document.getElementById("area-list");
        if (areaList) areaList.classList.add("submitting");

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
        } finally {
            this._isSubmitting = false;
            if (areaList) areaList.classList.remove("submitting");
        }
    }

    async createTurn(dni, areaId, email, notes) {
        return this._jsonRpc(`${this._getBasePath()}/api/turn/create`, {
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
        if (!response.ok) {
            throw new Error(
                `Error del servidor (${response.status}). Intente nuevamente.`
            );
        }
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
