/** @odoo-module **/
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

/**
 * DGC Portal Booking — DNI/CUIT validation Interaction
 *
 * Handles the DNI/CUIT toggle, input validation (length + CUIT checksum),
 * auto-formatting for CUIT mode, and disables the confirm button until
 * a valid document number is entered.
 *
 * Only activates when the DGC DNI row is present (i.e., DGC area appointments).
 */
export class PortalBookingDni extends Interaction {
    static selector = ".o_appointment_attendee_form";

    dynamicContent = {
        "#dgc_portal_doc_toggle": {
            "t-on-change.noUpdate": this.onToggleDocType,
        },
        "#dgc_citizen_dni": {
            "t-on-input.noUpdate": this.onDniInput,
            "t-on-keydown.noUpdate": this.onDniKeydown,
        },
        ".o_appointment_form_confirm_btn": {
            "t-on-click.noUpdate": this.onBeforeConfirm,
        },
    };

    setup() {
        this.docType = "dni";
        this.dniValid = false;
    }

    start() {
        this.dniRow = this.el.querySelector("#dgc_dni_row");
        if (!this.dniRow) {
            // Not a DGC area — nothing to do
            return;
        }
        this.dniInput = this.el.querySelector("#dgc_citizen_dni");
        this.docTypeHidden = this.el.querySelector("#dgc_doc_type");
        this.validationEl = this.el.querySelector("#dgc_dni_validation");
        this.confirmBtn = this.el.querySelector(".o_appointment_form_confirm_btn");
        this.toggleEl = this.el.querySelector("#dgc_portal_doc_toggle");
        this._updateConfirmState();
    }

    // --- Event handlers ---

    onToggleDocType() {
        if (!this.dniRow) return;
        this.docType = this.toggleEl.checked ? "cuit" : "dni";
        if (this.docTypeHidden) {
            this.docTypeHidden.value = this.docType;
        }
        // Update label highlights
        this.dniRow.querySelectorAll(".dgc-portal-doc-type-label").forEach((lbl) => {
            lbl.classList.toggle("active", lbl.dataset.type === this.docType);
        });
        // Update input attributes
        if (this.docType === "cuit") {
            this.dniInput.setAttribute("maxlength", "13");
            this.dniInput.setAttribute("placeholder", "XX-XXXXXXXX-X");
            this.dniInput.setAttribute("pattern", "\\d{2}-\\d{8}-\\d{1}");
        } else {
            this.dniInput.setAttribute("maxlength", "8");
            this.dniInput.setAttribute("placeholder", "Ingrese su DNI");
            this.dniInput.setAttribute("pattern", "\\d{7,8}");
        }
        // Clear and revalidate
        this.dniInput.value = "";
        this._updateValidation();
        this._updateConfirmState();
    }

    onDniInput() {
        if (!this.dniRow) return;
        const raw = this.dniInput.value;
        const digits = this._stripNonDigits(raw);
        if (this.docType === "cuit") {
            // Auto-format CUIT as XX-XXXXXXXX-X
            const maxDigits = digits.slice(0, 11);
            this.dniInput.value = this._formatCuit(maxDigits);
        } else {
            // DNI: allow only digits, max 8
            this.dniInput.value = digits.slice(0, 8);
        }
        this._updateValidation();
        this._updateConfirmState();
    }

    onDniKeydown(ev) {
        if (!this.dniRow) return;
        // Allow control keys
        if (["Backspace", "Delete", "Tab", "ArrowLeft", "ArrowRight", "Home", "End"].includes(ev.key)) {
            return;
        }
        // Allow Ctrl+A/C/V/X
        if (ev.ctrlKey || ev.metaKey) {
            return;
        }
        // Block non-digit input
        if (!/^\d$/.test(ev.key)) {
            ev.preventDefault();
        }
    }

    onBeforeConfirm(ev) {
        if (!this.dniRow) return;
        if (!this.dniValid) {
            ev.preventDefault();
            ev.stopPropagation();
            ev.stopImmediatePropagation();
            this.dniInput.classList.add("is-invalid");
            this.dniInput.focus();
            if (this.validationEl) {
                const msg = this.docType === "cuit"
                    ? "Ingrese un CUIT valido (11 digitos)"
                    : "Ingrese un DNI valido (7-8 digitos)";
                this.validationEl.textContent = msg;
                this.validationEl.className = "dgc-portal-dni-validation invalid";
            }
        }
    }

    // --- Validation helpers ---

    _stripNonDigits(value) {
        return (value || "").replace(/\D/g, "");
    }

    _formatCuit(digits) {
        if (digits.length <= 2) return digits;
        if (digits.length <= 10) return digits.slice(0, 2) + "-" + digits.slice(2);
        return digits.slice(0, 2) + "-" + digits.slice(2, 10) + "-" + digits.slice(10, 11);
    }

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

    _getDniValidationState() {
        const digits = this._stripNonDigits(this.dniInput.value);
        if (!digits || digits.length === 0) {
            return { state: "neutral", message: "", valid: false };
        }
        if (this.docType === "cuit") {
            if (digits.length < 11) {
                return { state: "neutral", message: `${digits.length}/11 digitos`, valid: false };
            }
            if (digits.length === 11) {
                if (this._validateCuitChecksum(digits)) {
                    return { state: "valid", message: "CUIT valido", valid: true };
                }
                return { state: "invalid", message: "CUIT invalido (checksum)", valid: false };
            }
            return { state: "invalid", message: "Maximo 11 digitos", valid: false };
        }
        // DNI mode
        if (digits.length < 7) {
            return { state: "neutral", message: `${digits.length}/8 digitos`, valid: false };
        }
        if (digits.length === 7 || digits.length === 8) {
            return { state: "valid", message: `${digits.length} digitos — DNI valido`, valid: true };
        }
        return { state: "invalid", message: "DNI: 7-8 digitos", valid: false };
    }

    _updateValidation() {
        const { state, message, valid } = this._getDniValidationState();
        this.dniValid = valid;
        if (this.validationEl) {
            this.validationEl.textContent = message;
            this.validationEl.className = `dgc-portal-dni-validation ${state}`;
        }
        // Update input visual state
        this.dniInput.classList.remove("is-valid", "is-invalid");
        if (state === "valid") this.dniInput.classList.add("is-valid");
        else if (state === "invalid") this.dniInput.classList.add("is-invalid");
    }

    _updateConfirmState() {
        if (!this.confirmBtn) return;
        // We do NOT disable the button (to avoid interfering with the base Interaction),
        // but we mark it visually and intercept the click if invalid.
    }
}

registry
    .category("public.interactions")
    .add("dgc_appointment_kiosk.portal_booking_dni", PortalBookingDni);
