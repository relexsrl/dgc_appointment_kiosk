/**
 * DGC Display - Waiting Room Queue Display
 * Vanilla JS - runs on public pages without Odoo web client
 */
class DgcDisplay {
    constructor() {
        this.body = document.body;
        this.refreshInterval = parseInt(this.body.dataset.refreshInterval || "30", 10);
        this.audioContext = null;
        this.soundEnabled = false;
        this.pollTimer = null;

        this._initSoundButton();
        this._startPolling();
    }

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

    _startPolling() {
        this._poll();
        this.pollTimer = setInterval(() => this._poll(), this.refreshInterval * 1000);
    }

    async _poll() {
        try {
            const data = await this._jsonRpc("/display/api/turns");
            this.updateCallingTurns(data.calling || []);
            this.updateWaitingList(data.waiting || []);
            this.updateMessages(data.scroll_messages || []);
        } catch {
            // Silent fail - will retry on next poll
        }
    }

    updateCallingTurns(calling) {
        const section = document.getElementById("calling-section");
        const turnEl = document.getElementById("calling-turn");
        if (!turnEl) return;

        if (calling.length === 0) {
            turnEl.innerHTML = '<span class="calling-number">---</span>';
            section.classList.remove("blink-slow", "blink-normal", "blink-fast");
            return;
        }

        const latest = calling[0];
        const currentNumber = turnEl.dataset.turnNumber;

        // Build display for all calling turns
        let html = "";
        for (const turn of calling) {
            const countClass = `call-count-${Math.min(turn.call_count, 3)}`;
            html += `
                <div class="calling-item ${countClass}">
                    <span class="calling-number">${this._escapeHtml(turn.turn_number)}</span>
                    <span class="calling-area">${this._escapeHtml(turn.area_name)}</span>
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
            tbody.innerHTML = '<tr><td colspan="2" class="no-waiting">No hay turnos en espera</td></tr>';
            return;
        }

        tbody.innerHTML = waiting.map((turn) => `
            <tr>
                <td>${this._escapeHtml(turn.turn_number)}</td>
                <td>${this._escapeHtml(turn.area_name)}</td>
            </tr>
        `).join("");
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
