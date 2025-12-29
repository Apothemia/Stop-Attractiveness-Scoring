class WeightSplitterBar {
    constructor() {
        this.bar = document.getElementById('weights-bar');
        this.h1 = document.getElementById('weights-handle-1');
        this.h2 = document.getElementById('weights-handle-2');

        this.seg1 = document.getElementById('weights-seg-1');
        this.seg2 = document.getElementById('weights-seg-2');
        this.seg3 = document.getElementById('weights-seg-3');

        this.w1Input = document.getElementById('w1-input');
        this.w2Input = document.getElementById('w2-input');
        this.w3Input = document.getElementById('w3-input');

        this.w1Label = document.getElementById('w1-label');
        this.w2Label = document.getElementById('w2-label');
        this.w3Label = document.getElementById('w3-label');

        this.a = 1 / 3;
        this.b = 2 / 3;

        this.dragging = null;

        if (!this.bar || !this.h1 || !this.h2) return;

        this.attach();
        this.render();
    }

    attach() {
        const onPointerDown = (handle, which) => (e) => {
            e.preventDefault();
            this.dragging = which;
            handle.setPointerCapture?.(e.pointerId);
        };

        const onPointerUp = () => {
            this.dragging = null;
        };

        const onPointerMove = (e) => {
            if (!this.dragging) return;
            const rect = this.bar.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width;
            const clamped = Math.min(1, Math.max(0, x));

            if (this.dragging === 'a') {
                const minGap = 0.02;
                this.a = Math.min(this.b - minGap, clamped);
            } else if (this.dragging === 'b') {
                const minGap = 0.02;
                this.b = Math.max(this.a + minGap, clamped);
            }

            this.render();
        };

        this.h1.addEventListener('pointerdown', onPointerDown(this.h1, 'a'));
        this.h2.addEventListener('pointerdown', onPointerDown(this.h2, 'b'));
        window.addEventListener('pointerup', onPointerUp);
        window.addEventListener('pointermove', onPointerMove);

        // Click-to-move nearest handle
        this.bar.addEventListener('pointerdown', (e) => {
            if (e.target === this.h1 || e.target === this.h2) return;
            const rect = this.bar.getBoundingClientRect();
            const x = Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width));
            const da = Math.abs(x - this.a);
            const db = Math.abs(x - this.b);
            this.dragging = da <= db ? 'a' : 'b';
            const fakeMove = new PointerEvent('pointermove', {clientX: e.clientX});
            window.dispatchEvent(fakeMove);
            this.dragging = null;
        });
    }

    getWeights() {
        const w1 = this.a;
        const w2 = this.b - this.a;
        const w3 = 1 - this.b;

        const s = w1 + w2 + w3;
        return {w1: w1 / s, w2: w2 / s, w3: w3 / s};
    }

    render() {
        const {w1, w2, w3} = this.getWeights();

        const aPct = w1 * 100;
        const bPct = (w1 + w2) * 100;

        this.seg1.style.left = `0%`;
        this.seg1.style.width = `${aPct}%`;

        this.seg2.style.left = `${aPct}%`;
        this.seg2.style.width = `${w2 * 100}%`;

        this.seg3.style.left = `${bPct}%`;
        this.seg3.style.width = `${w3 * 100}%`;

        this.h1.style.left = `${aPct}%`;
        this.h2.style.left = `${bPct}%`;

        this.w1Input.value = w1.toFixed(4);
        this.w2Input.value = w2.toFixed(4);
        this.w3Input.value = w3.toFixed(4);

        this.w1Label.textContent = w1.toFixed(2);
        this.w2Label.textContent = w2.toFixed(2);
        this.w3Label.textContent = w3.toFixed(2);

                window.dispatchEvent(new CustomEvent('weights-updated', { detail: { w1, w2, w3 } }));
    }
}

class AttractivenessScorerUI {
    constructor() {
        this.startDateInput = document.getElementById('start-date');
        this.endDateInput = document.getElementById('end-date');

        this.btn = document.getElementById('compute-scores-button');
        this.status = document.getElementById('scores-status');
        this.output = document.getElementById('scores-output');

        this.w1Input = document.getElementById('w1-input');
        this.w2Input = document.getElementById('w2-input');
        this.w3Input = document.getElementById('w3-input');

        this.splitter = new WeightSplitterBar();

        if (this.btn) {
            this.btn.addEventListener('click', () => this.compute());
        }
    }

    setStatus(text) {
        if (this.status) this.status.textContent = text || '';
    }

    renderTable(results) {
        if (!this.output) return;

        const rows = results.slice(0, 20).map(r => `
            <tr>
                <td>${r.abbr}</td>
                <td>${Number(r.as).toFixed(3)}</td>
                <td>${Number(r.board).toFixed(3)}</td>
                <td>${Number(r.eff_dst).toFixed(3)}</td>
                <td>${Number(r.access).toFixed(3)}</td>
            </tr>
        `).join('');

        this.output.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>Station</th>
                        <th>AS</th>
                        <th>Board</th>
                        <th>EffDst</th>
                        <th>Access</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
            <div style="margin-top:8px; opacity:0.85;">
                Showing top ${Math.min(20, results.length)} of ${results.length}.
            </div>
        `;
    }

    async compute() {
        const start = this.startDateInput?.value;
        const end = this.endDateInput?.value;

        if (!start || !end) {
            this.setStatus('Select start and end dates first.');
            return;
        }

        const w1 = this.w1Input?.value ?? '0.3333';
        const w2 = this.w2Input?.value ?? '0.3333';
        const w3 = this.w3Input?.value ?? '0.3334';

        this.setStatus('Computing scores...');
        if (this.btn) this.btn.disabled = true;

        try {
            const url =
                `/api/station-scores/?start_date=${encodeURIComponent(start)}`
                + `&end_date=${encodeURIComponent(end)}`
                + `&w1=${encodeURIComponent(w1)}`
                + `&w2=${encodeURIComponent(w2)}`
                + `&w3=${encodeURIComponent(w3)}`;

            const res = await fetch(url);
            const data = await res.json();

            if (!res.ok) {
                this.setStatus(data?.error || `HTTP error ${res.status}`);
                return;
            }

            this.setStatus(
                `Computed ${data.count} stations for ${data.start_date} → ${data.end_date} `
                + `(w1=${data.weights.w1.toFixed(2)}, w2=${data.weights.w2.toFixed(2)}, w3=${data.weights.w3.toFixed(2)}).`
            );
            this.renderTable(data.results || []);

            window.lastStationScores = data;
            window.dispatchEvent(new CustomEvent('station-scores-updated', { detail: data }));
        } catch (e) {
            console.error(e);
            this.setStatus('Failed to compute scores. See console for details.');
        } finally {
            if (this.btn) this.btn.disabled = false;
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new AttractivenessScorerUI();
});