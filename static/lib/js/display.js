/**
 * DGC Display - Waiting Room Queue Display
 * Vanilla JS - runs on public pages without Odoo web client
 */
class DgcDisplay {
    constructor() {
        this.body = document.body;
        this.token = this.body.dataset.token;
        this.refreshInterval = parseInt(this.body.dataset.refreshInterval || "30", 10);
        this.audioContext = null;
        this.soundEnabled = false;
        this.pollTimer = null;

        this._initSoundButton();
        this.startClock();
        this._startPolling();
    }

    // ---------------------------------------------------------------
    // Sound
    // ---------------------------------------------------------------
    _initSoundButton() {
        const overlay = document.getElementById("sound-overlay");
        const btn = document.getElementById("btn-activate-sound");
        if (btn) {
            btn.addEventListener("click", () => {
                try {
                    this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
                    this.soundEnabled = true;
                    if (overlay) overlay.style.display = "none";
                } catch {
                    // AudioContext not supported
                    if (overlay) overlay.style.display = "none";
                }
            });
        }
    }

    playCallSound() {
        if (!this.soundEnabled || !this.audioContext) return;

        const tones = [440, 440, 440]; // 3 beeps at 440Hz
        const duration = 0.2; // 200ms each
        const gap = 0.1; // 100ms gap

        tones.forEach((freq, i) => {
            const startTime = this.audioContext.currentTime + i * (duration + gap);
            const osc = this.audioContext.createOscillator();
            const gain = this.audioContext.createGain();

            osc.type = "sine";
            osc.frequency.value = freq;
            gain.gain.value = 0.5;

            osc.connect(gain);
            gain.connect(this.audioContext.destination);

            osc.start(startTime);
            osc.stop(startTime + duration);
        });
    }

    // ---------------------------------------------------------------
    // Clock
    // ---------------------------------------------------------------
    startClock() {
        const updateClock = () => {
            const now = new Date();
            const el = document.getElementById("display-clock");
            if (el) {
                el.textContent = now.toLocaleTimeString("es-AR", {
                    hour: "2-digit",
                    minute: "2-digit",
                });
            }
        };
        updateClock();
        setInterval(updateClock, 1000);
    }

    // ---------------------------------------------------------------
    // Polling
    // ---------------------------------------------------------------
    _updateConnectionStatus(status) {
        // status: 'bus', 'polling', 'disconnected'
        const el = document.getElementById('connection-status');
        if (!el) return;
        const dot = el.querySelector('.status-dot');
        const label = el.querySelector('.status-label');
        if (dot) {
            dot.className = 'status-dot ' + status;
        }
        if (label) {
            const labels = {
                polling: 'Conectado',
                disconnected: 'Sin conexión',
            };
            label.textContent = labels[status] || status;
        }
    }

    _startPolling() {
        if (this.pollTimer) return;
        console.info("[DgcDisplay] Starting interval polling");
        this._updateConnectionStatus('polling');
        this._loadTurns();
        this.pollTimer = setInterval(
            () => this._loadTurns(),
            this.refreshInterval * 1000
        );
    }

    // ---------------------------------------------------------------
    // Data loading
    // ---------------------------------------------------------------
    async _loadTurns() {
        try {
            if (!this.token) {
                console.error("No token found in body data-token attribute");
                return;
            }
            const data = await this._jsonRpc(`/display/${this.token}/api/turns`);
            this.updateCallingTurns(data.calling || []);
            this.updateWaitingList(data.waiting || []);
            this.updateMessages(data.scroll_messages || []);
            this._updateConnectionStatus('polling');
        } catch (e) {
            console.warn("Polling error:", e);
            this._updateConnectionStatus('disconnected');
        }
    }

    updateCallingTurns(calling) {
        const section = document.getElementById("calling-section");
        const turnEl = document.getElementById("calling-turn");
        if (!turnEl) return;

        if (calling.length === 0) {
            turnEl.innerHTML = '<div class="calling-dni">---</div>';
            section.classList.remove("blink-slow", "blink-normal", "blink-fast");
            return;
        }

        const latest = calling[0];
        const currentNumber = turnEl.dataset.turnNumber;

        // Build display for all calling turns
        let html = "";
        for (const turn of calling) {
            const countClass = `call-count-${Math.min(turn.call_count, 3)}`;
            // Use citizen_dni as primary identifier; fall back to turn_number
            // DNI is always stored as base 7-8 digit number (CUIT is normalized on the server)
            const displayDni = turn.citizen_dni || "";
            const primaryId = displayDni
                ? this._escapeHtml(displayDni)
                : this._escapeHtml(turn.turn_number);
            const boxHtml = turn.operator_box
                ? `<div class="calling-box">Ventanilla ${this._escapeHtml(turn.operator_box)}</div>`
                : "";
            const colorStyle = turn.area_color
                ? `border-left: 6px solid ${this._escapeHtml(turn.area_color)}`
                : "";
            html += `
                <div class="calling-item ${countClass}" style="${colorStyle}">
                    <div class="calling-dni">${primaryId}</div>
                    <div class="calling-meta">
                        <span class="calling-turnnum">${this._escapeHtml(turn.turn_number)}</span>
                        <span class="calling-area">${this._escapeHtml(turn.area_name)}</span>
                    </div>
                    ${boxHtml}
                </div>
            `;
        }
        turnEl.innerHTML = html;
        turnEl.dataset.turnNumber = latest.turn_number;

        // Play sound on new call
        if (currentNumber !== latest.turn_number) {
            this.playCallSound();
            section.classList.add("blink-normal");
            setTimeout(() => section.classList.remove("blink-normal"), 3000);
        }
    }

    updateWaitingList(waiting) {
        const tbody = document.getElementById("waiting-list-body");
        if (!tbody) return;

        if (waiting.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" class="no-waiting">No hay turnos en espera</td></tr>';
            return;
        }

        tbody.innerHTML = waiting.map((turn) => {
            const colorDot = turn.area_color
                ? `<span class="area-color-dot" style="background:${this._escapeHtml(turn.area_color)}"></span>`
                : "";
            return `
            <tr>
                <td>${this._escapeHtml(turn.turn_number)}</td>
                <td>${colorDot}${this._escapeHtml(turn.area_name)}</td>
            </tr>
        `;
        }).join("");
    }

    updateMessages(messages) {
        const content = document.getElementById("message-content");
        if (!content || messages.length === 0) return;
        content.textContent = messages.join("  ·  ");
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
        // Check for HTTP errors (like 404) before parsing JSON
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        if (data.error) {
            throw new Error(data.error.message || "Server error");
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
    new DgcDisplay();
});
