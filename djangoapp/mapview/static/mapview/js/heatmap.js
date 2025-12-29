(function () {
    function clamp01(x) {
        return Math.min(1, Math.max(0, x));
    }

    // Yellow (low) -> Red (high)
    function yellowToRed(t) {
        t = clamp01(t);
        const r = 255;
        const g = Math.round(255 * (1 - t));
        const b = 0;
        return `rgb(${r},${g},${b})`;
    }

    function computeMinMax(values) {
        let min = Infinity;
        let max = -Infinity;
        for (const v of values) {
            if (typeof v !== 'number' || Number.isNaN(v)) continue;
            if (v < min) min = v;
            if (v > max) max = v;
        }
        if (!Number.isFinite(min) || !Number.isFinite(max)) return null;
        return {min, max};
    }

    function norm(v, min, max) {
        if (max === min) return 0;
        return (v - min) / (max - min);
    }

    class StationHeatmap {
        constructor() {
            this.select = document.getElementById('heatmap-metric');
            this.layer = null;
            this.circlesByAbbr = new Map();
            this.stationsByAbbr = new Map(); // abbr -> {lat, lon}

            if (this.select) {
                this.select.addEventListener('change', () => this.apply());
            }

            window.addEventListener('station-scores-updated', () => this.apply());

            this.ensureMapThenInit();
        }

        ensureMapThenInit() {
            const tryInit = async () => {
                if (!window.L || !window.map) return false;

                if (!this.layer) {
                    this.layer = window.L.layerGroup().addTo(window.map);
                }
                if (this.stationsByAbbr.size === 0) {
                    await this.loadStations();
                }
                return true;
            };

            const tick = async () => {
                const ok = await tryInit();
                if (!ok) {
                    window.setTimeout(tick, 150);
                }
            };
            tick();
        }

        async loadStations() {
            const res = await fetch('/api/stations/');
            const data = await res.json();
            for (const s of data) {
                if (!s?.abbr) continue;
                this.stationsByAbbr.set(s.abbr, {lat: s.lat, lon: s.lon});
            }
        }

        clear() {
            if (!this.layer) return;
            this.layer.clearLayers();
            this.circlesByAbbr.clear();
        }

        ensureCircle(abbr, lat, lon) {
            if (!this.layer) return null;
            const existing = this.circlesByAbbr.get(abbr);
            if (existing) return existing;

            const circle = window.L.circleMarker([lat, lon], {
                radius: 10,
                weight: 1,
                color: 'rgba(0,0,0,0.5)',
                opacity: 0.8,
                fillOpacity: 0.75,
                fillColor: 'rgb(255,255,0)',
            });

            circle.bindTooltip(abbr, {direction: 'top', offset: [0, -6]});

            circle.addTo(this.layer);
            this.circlesByAbbr.set(abbr, circle);
            return circle;
        }

        apply() {
            const metric = this.select?.value || 'none';
            const scorePayload = window.lastStationScores;
            const results = scorePayload?.results || [];

            if (!this.layer) return;

            if (metric === 'none') {
                this.clear();
                return;
            }

            if (!results.length) {
                this.clear();
                return;
            }

            const values = results
                .map(r => r?.[metric])
                .filter(v => typeof v === 'number' && !Number.isNaN(v));

            const mm = computeMinMax(values);
            if (!mm) {
                this.clear();
                return;
            }

            const keep = new Set();

            for (const r of results) {
                const abbr = r?.abbr;
                const v = r?.[metric];
                if (!abbr || typeof v !== 'number' || Number.isNaN(v)) continue;

                const loc = this.stationsByAbbr.get(abbr);
                if (!loc) continue;

                const t = norm(v, mm.min, mm.max);
                const color = yellowToRed(t);

                const circle = this.ensureCircle(abbr, loc.lat, loc.lon);
                if (!circle) continue;

                circle.setStyle({fillColor: color});
                circle.setTooltipContent(`${abbr} — ${metric}: ${v.toFixed(3)}`);

                keep.add(abbr);
            }

            for (const [abbr, circle] of this.circlesByAbbr.entries()) {
                if (!keep.has(abbr)) {
                    this.layer.removeLayer(circle);
                    this.circlesByAbbr.delete(abbr);
                }
            }
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        new StationHeatmap();
    });
})();