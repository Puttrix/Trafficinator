// Backfill Manager: one-off historical runs
class BackfillManager {
    constructor() {
        this.form = document.getElementById('backfill-form');
        this.errorBox = document.getElementById('backfill-error');
        this.resultBox = document.getElementById('backfill-result');
        this.resultMessage = document.getElementById('backfill-result-message');
        this.resultContainer = document.getElementById('backfill-result-container');
        this.resultId = document.getElementById('backfill-result-id');
        this.runsTable = document.getElementById('backfill-runs-table');
        this.runsBody = document.getElementById('backfill-runs-body');
        this.cleanupBtn = document.getElementById('backfill-cleanup-btn');
        this.lastTimestampEl = document.getElementById('backfill-last-timestamp');
        this.loadLastBtn = document.getElementById('backfill-load-last-btn');
        this.lastPayload = null;
    }

    init() {
        if (!this.form) return;

        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.runBackfill();
        });

        if (this.cleanupBtn) {
            this.cleanupBtn.addEventListener('click', () => this.cleanupRuns());
        }

        if (this.loadLastBtn) {
            this.loadLastBtn.addEventListener('click', () => this.applyLastPayload());
        }
    }

    onTabActivated() {
        this.clearResult();
        this.loadStatus();
    }

    onTabDeactivated() {
        // No-op for now
    }

    async loadStatus() {
        this.clearResult();
        try {
            const [status, last] = await Promise.all([
                api.backfillStatus(),
                api.backfillLast(),
            ]);
            this.renderRuns(status.runs || []);
            this.showLast(last);
        } catch (error) {
            UI.showAlert(error.message || 'Failed to load backfill status', 'error');
        }
    }

    clearResult() {
        if (this.resultBox) {
            this.resultBox.classList.add('hidden');
        }
        if (this.errorBox) {
            this.errorBox.classList.add('hidden');
            this.errorBox.textContent = '';
        }
    }

    getValue(id) {
        const el = document.getElementById(id);
        return el ? el.value.trim() : '';
    }

    setValue(id, value) {
        const el = document.getElementById(id);
        if (el !== null && value !== undefined && value !== null) {
            el.value = value;
        }
    }

    parseDate(str) {
        if (!str) return null;
        const [y, m, d] = str.split('-').map(Number);
        if (!y || !m || !d) return null;
        return new Date(Date.UTC(y, m - 1, d));
    }

    getNumber(id) {
        const raw = this.getValue(id);
        if (raw === '') return null;
        const num = Number(raw);
        return Number.isFinite(num) ? num : null;
    }

    buildPayload() {
        const payload = {};

        const start = this.getValue('backfill_start_date');
        const end = this.getValue('backfill_end_date');
        const daysBack = this.getNumber('backfill_days_back');
        const duration = this.getNumber('backfill_duration_days');
        const maxPerDay = this.getNumber('backfill_max_per_day');
        const maxTotal = this.getNumber('backfill_max_total');
        const rps = this.getNumber('backfill_rps_limit');
        const seed = this.getNumber('backfill_seed');
        const name = this.getValue('backfill_name');
        const runOnce = document.getElementById('backfill_run_once')?.checked ?? true;

        if (start) payload.BACKFILL_START_DATE = start;
        if (end) payload.BACKFILL_END_DATE = end;
        if (daysBack !== null) payload.BACKFILL_DAYS_BACK = daysBack;
        if (duration !== null) payload.BACKFILL_DURATION_DAYS = duration;
        if (maxPerDay !== null) payload.BACKFILL_MAX_VISITS_PER_DAY = maxPerDay;
        if (maxTotal !== null) payload.BACKFILL_MAX_VISITS_TOTAL = maxTotal;
        if (rps !== null && rps > 0) payload.BACKFILL_RPS_LIMIT = rps;
        if (seed !== null) payload.BACKFILL_SEED = seed;
        if (name) payload.name = name;
        payload.BACKFILL_RUN_ONCE = runOnce;

        // If absolute dates are provided, drop relative fields; if relative provided, drop absolute
        const hasAbsolute = payload.BACKFILL_START_DATE || payload.BACKFILL_END_DATE;
        const hasRelative = payload.BACKFILL_DAYS_BACK !== undefined || payload.BACKFILL_DURATION_DAYS !== undefined;
        if (hasAbsolute && hasRelative) {
            // Prefer absolute if both were filled in
            delete payload.BACKFILL_DAYS_BACK;
            delete payload.BACKFILL_DURATION_DAYS;
        }

        return payload;
    }

    validatePayload(payload) {
        const hasAbsolute = payload.BACKFILL_START_DATE || payload.BACKFILL_END_DATE;
        const hasRelative = payload.BACKFILL_DAYS_BACK !== undefined || payload.BACKFILL_DURATION_DAYS !== undefined;

        // Require one strategy (absolute OR relative), not both
        if (!hasAbsolute && !hasRelative) {
            throw new Error('Provide either absolute dates (start + end) or relative window (days back + duration).');
        }

        if (hasAbsolute && hasRelative) {
            throw new Error('Use absolute dates OR relative window, not both.');
        }

        if (hasAbsolute) {
            if (!payload.BACKFILL_START_DATE || !payload.BACKFILL_END_DATE) {
                throw new Error('Both BACKFILL_START_DATE and BACKFILL_END_DATE are required for absolute mode.');
            }
        }

        if (hasRelative) {
            if (payload.BACKFILL_DAYS_BACK === undefined || payload.BACKFILL_DURATION_DAYS === undefined) {
                throw new Error('Both BACKFILL_DAYS_BACK and BACKFILL_DURATION_DAYS are required for relative mode.');
            }
        }

        // Absolute window constraints: no future end, window <= 180 days
        if (hasAbsolute) {
            const start = this.parseDate(payload.BACKFILL_START_DATE);
            const end = this.parseDate(payload.BACKFILL_END_DATE);
            if (!start || !end) {
                throw new Error('Dates must be in YYYY-MM-DD format.');
            }
            const today = new Date();
            const todayUtc = new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate()));
            if (end > todayUtc) {
                throw new Error('End date cannot be in the future.');
            }
            const diffDays = (end - start) / (1000 * 60 * 60 * 24) + 1;
            if (diffDays > 180) {
                throw new Error('Backfill window cannot exceed 180 days.');
            }
            if (diffDays <= 0) {
                throw new Error('End date must be on or after start date.');
            }
        }

        // Relative window constraints: duration positive and <= 180
        if (hasRelative) {
            if (payload.BACKFILL_DURATION_DAYS <= 0) {
                throw new Error('Duration must be > 0.');
            }
            if (payload.BACKFILL_DURATION_DAYS > 180) {
                throw new Error('Duration cannot exceed 180 days.');
            }
        }
    }

    async runBackfill() {
        const payload = this.buildPayload();

        try {
            this.validatePayload(payload);
            UI.showLoading('Starting backfill run...');
            const response = await api.runBackfill(payload);
            UI.hideLoading();

            this.showResult(response);
            UI.showAlert(response.message || 'Backfill job started', 'success');
            await this.loadStatus();
        } catch (error) {
            UI.hideLoading();
            this.showError(error.message || 'Failed to start backfill');
        }
    }

    showResult(response) {
        if (!this.resultBox) return;
        this.resultMessage.textContent = response.message || '—';
        this.resultContainer.textContent = response.container_name || '—';
        this.resultId.textContent = response.container_id || '—';
        this.resultBox.classList.remove('hidden');
        if (response.timestamp && this.lastTimestampEl) {
            this.lastTimestampEl.textContent = response.timestamp;
        }
    }

    renderRuns(runs) {
        if (!this.runsBody || !this.runsTable) return;
        this.runsBody.innerHTML = '';
        if (!runs.length) {
            this.runsTable.classList.add('hidden');
            return;
        }
        this.runsTable.classList.remove('hidden');
        runs.forEach((run) => {
            const tr = document.createElement('tr');
            tr.className = 'border-b border-gray-200';
            tr.innerHTML = `
                <td class="px-3 py-2 text-xs font-mono text-gray-700">${run.container_name || '—'}</td>
                <td class="px-3 py-2 text-xs font-mono text-gray-500">${run.container_id || '—'}</td>
                <td class="px-3 py-2 text-xs">${run.state || '—'}</td>
                <td class="px-3 py-2 text-xs text-gray-500">${run.started_at || '—'}</td>
                <td class="px-3 py-2 text-xs text-gray-500">${run.finished_at || '—'}</td>
                <td class="px-3 py-2 text-xs">${run.exit_code ?? '—'}</td>
                <td class="px-3 py-2 text-xs">
                    ${run.state === 'running' ? `<button data-cancel="${run.container_name}" class="text-red-600 hover:underline text-xs">Cancel</button>` : '—'}
                </td>
            `;
            this.runsBody.appendChild(tr);
        });

        // Wire cancel buttons
        this.runsBody.querySelectorAll('button[data-cancel]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const name = e.currentTarget.getAttribute('data-cancel');
                if (name) {
                    this.cancelRun(name);
                }
            });
        });
    }

    async cleanupRuns() {
        try {
            UI.showLoading('Cleaning up completed runs...');
            const res = await api.backfillCleanup();
            UI.hideLoading();
            if (res.success) {
                UI.showAlert(res.message || 'Cleanup complete', 'success');
            } else {
                this.showError(res.message || 'Cleanup completed with errors');
            }
            await this.loadStatus();
        } catch (error) {
            UI.hideLoading();
            this.showError(error.message || 'Failed to clean up backfill runs');
        }
    }

    async cancelRun(containerName) {
        try {
            UI.showLoading('Stopping backfill...');
            const res = await api.backfillCancel(containerName);
            UI.hideLoading();
            if (res.success) {
                UI.showAlert(res.message || 'Backfill stopped', 'success');
            } else {
                this.showError(res.error || res.message || 'Failed to stop backfill');
            }
            await this.loadStatus();
        } catch (error) {
            UI.hideLoading();
            this.showError(error.message || 'Failed to stop backfill');
        }
    }

    showLast(last) {
        if (!last || !this.resultBox) return;
        if (!last.payload && !last.result) {
            return;
        }
        this.lastPayload = last.payload || null;
        this.resultMessage.textContent = last.message || '—';
        if (last.result) {
            this.resultContainer.textContent = last.result.container_name || '—';
            this.resultId.textContent = last.result.container_id || '—';
        }
        if (last.timestamp && this.lastTimestampEl) {
            this.lastTimestampEl.textContent = last.timestamp;
        }
        this.resultBox.classList.remove('hidden');
    }

    applyLastPayload() {
        if (!this.lastPayload) {
            UI.showAlert('No last backfill payload available to load.', 'warning');
            return;
        }
        // Absolute
        this.setValue('backfill_start_date', this.lastPayload.BACKFILL_START_DATE || '');
        this.setValue('backfill_end_date', this.lastPayload.BACKFILL_END_DATE || '');

        // Relative
        this.setValue('backfill_days_back', this.lastPayload.BACKFILL_DAYS_BACK ?? '');
        this.setValue('backfill_duration_days', this.lastPayload.BACKFILL_DURATION_DAYS ?? '');

        // Caps/throttle/seed
        this.setValue('backfill_max_per_day', this.lastPayload.BACKFILL_MAX_VISITS_PER_DAY ?? '');
        this.setValue('backfill_max_total', this.lastPayload.BACKFILL_MAX_VISITS_TOTAL ?? '');
        this.setValue('backfill_rps_limit', this.lastPayload.BACKFILL_RPS_LIMIT ?? '');
        this.setValue('backfill_seed', this.lastPayload.BACKFILL_SEED ?? '');

        // Run name/run once
        this.setValue('backfill_name', this.lastPayload.name ?? '');
        const runOnceEl = document.getElementById('backfill_run_once');
        if (runOnceEl) {
            runOnceEl.checked = (this.lastPayload.BACKFILL_RUN_ONCE ?? true) === true || this.lastPayload.BACKFILL_RUN_ONCE === 'true';
        }

        UI.showAlert('Last backfill payload loaded into form.', 'success');
    }

    showError(message) {
        if (this.errorBox) {
            this.errorBox.textContent = message;
            this.errorBox.classList.remove('hidden');
        } else {
            UI.showAlert(message, 'error');
        }
    }
}

// Export globally
window.BackfillManager = BackfillManager;
