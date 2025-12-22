// Status Dashboard Management
class StatusDashboard {
    constructor() {
        this.currentStatus = null;
        this.refreshInterval = null;
        this.isRefreshing = false;
        this.isLoadingPresets = false;
        this.latestPresetDetail = null;
    }

    // Initialize the status dashboard
    init() {
        this.setupEventListeners();
        this.loadStatus();
        this.refreshSavedPresets(true);
    }

    // Setup event listeners
    setupEventListeners() {
        // Start button
        const startBtn = document.getElementById('start-btn');
        if (startBtn) {
            startBtn.addEventListener('click', () => this.handleStart());
        }

        // Stop button
        const stopBtn = document.getElementById('stop-btn');
        if (stopBtn) {
            stopBtn.addEventListener('click', () => this.handleStop());
        }

        // Restart button
        const restartBtn = document.getElementById('restart-btn');
        if (restartBtn) {
            restartBtn.addEventListener('click', () => this.handleRestart());
        }

        const viewPresetsBtn = document.getElementById('view-presets-btn');
        if (viewPresetsBtn) {
            viewPresetsBtn.addEventListener('click', () => {
                UI.switchTab('presets');
                if (window.loadPresets) {
                    window.loadPresets.renderCustomPresets();
                }
            });
        }
    }

    // Load status from API
    async loadStatus() {
        if (this.isRefreshing) return;
        
        this.isRefreshing = true;
        
        try {
            const status = await api.getStatus();
            this.currentStatus = status;
            this.updateDashboard(status);
        } catch (error) {
            console.error('Failed to load status:', error);
            this.showError(error.message);
        } finally {
            this.isRefreshing = false;
        }
    }

    async refreshSavedPresets(showLoading = false) {
        const container = document.getElementById('status-saved-presets');
        if (!container || this.isLoadingPresets) {
            return;
        }

        this.isLoadingPresets = true;

        if (showLoading) {
            container.innerHTML = `
                <p class="text-sm text-gray-500">Loading saved presets...</p>
            `;
        }

        try {
            const response = await api.request('/api/presets');
            const presets = response.presets || [];

            if (!presets.length) {
                this.latestPresetDetail = null;
                container.innerHTML = `
                    <p class="text-sm text-gray-500">No saved presets yet. Save a configuration from the Config tab to reuse it later.</p>
                `;
                return;
            }

            let latestPresetDetail = null;
            try {
                latestPresetDetail = await api.request(`/api/presets/${presets[0].id}`);
            } catch (detailError) {
                console.error('Failed to load latest preset detail:', detailError);
            }
            this.latestPresetDetail = latestPresetDetail;
            if (latestPresetDetail && this.currentStatus && (!this.currentStatus.config || Object.keys(this.currentStatus.config).length === 0)) {
                this.updateMetrics(this.currentStatus);
                this.updateConfigDetails(this.currentStatus);
            }

            const limitedPresets = presets.slice(0, 3);
            const itemsHtml = limitedPresets.map((preset) => {
                const updatedDate = new Date(preset.updated_at);
                const updatedLabel = Number.isNaN(updatedDate.getTime())
                    ? preset.updated_at
                    : UI.formatTimestamp(updatedDate);

                return `
                    <div class="flex items-start justify-between gap-4 p-4 border border-gray-100 rounded-lg">
                        <div>
                            <p class="text-sm font-medium text-gray-900">${UI.escapeHtml(preset.name)}</p>
                            ${preset.description ? `<p class="text-xs text-gray-500 mt-1">${UI.escapeHtml(preset.description)}</p>` : ''}
                            <p class="text-xs text-gray-400 mt-1">Updated ${updatedLabel}</p>
                        </div>
                        <button
                            class="load-preset-from-status text-xs font-medium text-primary hover:text-blue-700"
                            data-preset-id="${preset.id}"
                            data-preset-name="${UI.escapeHtml(preset.name)}"
                            type="button"
                        >
                            Load
                        </button>
                    </div>
                `;
            }).join('');

            const moreCount = presets.length - limitedPresets.length;
            const footer = moreCount > 0
                ? `<p class="text-xs text-gray-400">+${moreCount} more saved preset${moreCount === 1 ? '' : 's'} — open the Presets tab to manage all.</p>`
                : '';

            container.innerHTML = `
                <div class="space-y-3">
                    ${itemsHtml}
                </div>
                ${footer ? `<div class="mt-3">${footer}</div>` : ''}
            `;

            container.querySelectorAll('.load-preset-from-status').forEach((button) => {
                button.addEventListener('click', async () => {
                    const presetId = parseInt(button.dataset.presetId, 10);
                    const presetName = button.dataset.presetName;

                    UI.confirm(
                        `Load "${presetName}" preset? This will populate the configuration form.`,
                        async () => {
                            try {
                                if (window.loadPresets) {
                                    await window.loadPresets.loadCustomPresetById(presetId);
                                }
                            } catch (error) {
                                UI.showAlert(`Failed to load preset: ${error.message}`, 'error');
                            }
                        }
                    );
                });
            });
        } catch (error) {
            console.error('Failed to load saved presets:', error);
            container.innerHTML = `
                <p class="text-sm text-red-600">Failed to load saved presets: ${UI.escapeHtml(error.message || 'Unknown error')}</p>
            `;
        } finally {
            this.isLoadingPresets = false;
        }
    }

    // Update dashboard with status data
    updateDashboard(status) {
        // Update status indicator
        this.updateStatusIndicator(status);
        
        // Update control buttons
        this.updateControlButtons(status);
        
        // Update metrics
        this.updateMetrics(status);
        
        // Update configuration details
        this.updateConfigDetails(status);

        // Update backfill summary
        this.updateBackfill(status);
    }

    // Update status indicator (icon, text, color)
    updateStatusIndicator(status) {
        const indicator = document.getElementById('status-indicator');
        const statusText = document.getElementById('status-text');
        const statusSubtitle = document.getElementById('status-subtitle');
        
        if (!indicator || !statusText || !statusSubtitle) return;

        const containerStatus = status.container?.state || status.status || 'unknown';
        
        // Clear existing classes
        indicator.className = 'flex items-center justify-center w-16 h-16 rounded-full';
        
        // Update based on status
        switch (containerStatus) {
            case 'running':
                indicator.classList.add('bg-green-100');
                indicator.innerHTML = `
                    <svg class="w-8 h-8 text-green-600 animate-pulse" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd"></path>
                    </svg>
                `;
                statusText.textContent = 'Running';
                statusText.className = 'text-2xl font-bold text-green-600';
                statusSubtitle.textContent = 'Load generator is active';
                break;
                
            case 'stopped':
            case 'exited':
                indicator.classList.add('bg-gray-100');
                indicator.innerHTML = `
                    <svg class="w-8 h-8 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clip-rule="evenodd"></path>
                    </svg>
                `;
                statusText.textContent = 'Stopped';
                statusText.className = 'text-2xl font-bold text-gray-600';
                statusSubtitle.textContent = 'Container is not running';
                break;
                
            case 'paused':
                indicator.classList.add('bg-yellow-100');
                indicator.innerHTML = `
                    <svg class="w-8 h-8 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd"></path>
                    </svg>
                `;
                statusText.textContent = 'Paused';
                statusText.className = 'text-2xl font-bold text-yellow-600';
                statusSubtitle.textContent = 'Container is paused';
                break;
                
            case 'error':
                indicator.classList.add('bg-red-100');
                indicator.innerHTML = `
                    <svg class="w-8 h-8 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
                    </svg>
                `;
                statusText.textContent = 'Error';
                statusText.className = 'text-2xl font-bold text-red-600';
                statusSubtitle.textContent = status.error || 'An error occurred';
                break;
                
            default:
                indicator.classList.add('bg-gray-100');
                indicator.innerHTML = `
                    <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                `;
                statusText.textContent = 'Unknown';
                statusText.className = 'text-2xl font-bold text-gray-600';
                statusSubtitle.textContent = 'Unable to determine status';
        }
    }

    // Update control buttons visibility and state
    updateControlButtons(status) {
        const startBtn = document.getElementById('start-btn');
        const stopBtn = document.getElementById('stop-btn');
        const restartBtn = document.getElementById('restart-btn');
        
        if (!startBtn || !stopBtn || !restartBtn) return;

        const containerStatus = status.container?.state || status.status || 'unknown';
        
        // Show/hide buttons based on status
        if (containerStatus === 'running' || containerStatus === 'paused') {
            startBtn.classList.add('hidden');
            stopBtn.classList.remove('hidden');
            restartBtn.classList.remove('hidden');
            startBtn.disabled = false;
            stopBtn.disabled = false;
            restartBtn.disabled = false;
        } else if (containerStatus === 'stopped' || containerStatus === 'exited' || containerStatus === 'created') {
            startBtn.classList.remove('hidden');
            stopBtn.classList.add('hidden');
            restartBtn.classList.add('hidden');
            startBtn.disabled = false;
            stopBtn.disabled = true;
            restartBtn.disabled = true;
        } else {
            // Unknown or error state - show all but disable
            startBtn.classList.remove('hidden');
            stopBtn.classList.remove('hidden');
            restartBtn.classList.remove('hidden');
            startBtn.disabled = true;
            stopBtn.disabled = true;
            restartBtn.disabled = true;
        }
    }

    // Update metrics cards
    updateMetrics(status) {
        // Uptime
        const uptimeEl = document.getElementById('metric-uptime');
        const uptimeDetailEl = document.getElementById('metric-uptime-detail');
        if (uptimeEl && uptimeDetailEl) {
            const uptime = status.stats?.uptime || status.container?.uptime;
            const startedAt = status.container?.started_at;
            
            if (uptime) {
                uptimeEl.textContent = uptime;
                if (startedAt) {
                    uptimeDetailEl.textContent = `Started ${UI.formatTimestamp(new Date(startedAt))}`;
                } else {
                    uptimeDetailEl.textContent = 'Running';
                }
            } else {
                uptimeEl.textContent = '--';
                uptimeDetailEl.textContent = 'Container not running';
            }
        }

        // Total visits
        const totalVisitsEl = document.getElementById('metric-total-visits');
        const totalVisitsDetailEl = document.getElementById('metric-total-visits-detail');
        if (totalVisitsEl && totalVisitsDetailEl) {
            const visitsGenerated = status.stats?.visits_generated;
            if (visitsGenerated !== null && visitsGenerated !== undefined) {
                totalVisitsEl.textContent = parseInt(visitsGenerated).toLocaleString();
                totalVisitsDetailEl.textContent = 'Total visits generated';
            } else {
                totalVisitsEl.textContent = '--';
                totalVisitsDetailEl.textContent = 'Metrics not available yet';
            }
        }

        // Current rate
        const rateEl = document.getElementById('metric-rate');
        const rateDetailEl = document.getElementById('metric-rate-detail');
        if (rateEl && rateDetailEl) {
            const currentRate = status.stats?.current_rate;
            if (currentRate) {
                rateEl.textContent = currentRate;
                rateDetailEl.textContent = 'Current visit rate';
            } else {
                rateEl.textContent = '--';
                rateDetailEl.textContent = 'Calculating...';
            }
        }

        // Daily target
        const targetEl = document.getElementById('metric-target');
        const targetDetailEl = document.getElementById('metric-target-detail');
        if (targetEl && targetDetailEl) {
            const targetVisits = this.getConfigValue(status, 'TARGET_VISITS_PER_DAY', null);
            if (targetVisits !== null && targetVisits !== undefined) {
                const numericTarget = Number(targetVisits);
                if (!Number.isNaN(numericTarget)) {
                    targetEl.textContent = numericTarget.toLocaleString();
                    targetDetailEl.textContent = `Target: ${numericTarget.toLocaleString()} /day`;
                } else {
                    targetEl.textContent = targetVisits;
                    targetDetailEl.textContent = 'Configured daily target';
                }
            } else {
                targetEl.textContent = '--';
                targetDetailEl.textContent = 'Target not configured';
            }
        }
    }

    // Update configuration details section
    updateConfigDetails(status) {
        const configDetailsEl = document.getElementById('config-details');
        if (!configDetailsEl) return;

        const hasStatusConfig = status.config && Object.keys(status.config).length > 0;
        const hasPresetConfig = this.latestPresetDetail?.config && Object.keys(this.latestPresetDetail.config).length > 0;

        if (!hasStatusConfig && !hasPresetConfig) {
            configDetailsEl.innerHTML = '<p class="text-sm text-gray-500 col-span-full">No configuration available</p>';
            return;
        }

        const keysToShow = [
            { key: 'MATOMO_URL', label: 'Matomo URL' },
            { key: 'MATOMO_SITE_ID', label: 'Site ID' },
            { key: 'TARGET_VISITS_PER_DAY', label: 'Target Visits/Day' },
            { key: 'CONCURRENCY', label: 'Concurrency' },
            { key: 'PAGEVIEWS_MIN', label: 'Pageviews Min' },
            { key: 'PAGEVIEWS_MAX', label: 'Pageviews Max' },
            { key: 'ECOMMERCE_PROBABILITY', label: 'Ecommerce %' },
            { key: 'RANDOMIZE_VISITOR_COUNTRIES', label: 'Geo Randomization' },
            { key: 'TIMEZONE', label: 'Timezone' },
        ];

        let html = '';
        keysToShow.forEach(({ key, label }) => {
            const value = this.getConfigValue(status, key);
            if (value !== null) {
                html += `
                    <div class="flex flex-col">
                        <span class="text-xs text-gray-500">${label}</span>
                        <span class="text-sm font-medium text-gray-900 mt-1">${this.formatConfigValue(key, value)}</span>
                    </div>
                `;
            }
        });

        if (html) {
            configDetailsEl.innerHTML = html;
        } else {
            configDetailsEl.innerHTML = '<p class="text-sm text-gray-500 col-span-full">Configuration not available</p>';
        }
    }

    // Get configuration value from status or saved presets
    getConfigValue(status, key, defaultValue = null) {
        if (status.config && Object.prototype.hasOwnProperty.call(status.config, key)) {
            const value = status.config[key];
            if (value !== undefined && value !== null && value !== '***MASKED***' && value !== '') {
                return value;
            }
        }

        const presetConfig = this.latestPresetDetail?.config;
        if (presetConfig) {
            const map = {
                MATOMO_URL: 'matomo_url',
                MATOMO_SITE_ID: 'matomo_site_id',
                MATOMO_TOKEN_AUTH: 'matomo_token_auth',
                TARGET_VISITS_PER_DAY: 'target_visits_per_day',
                PAGEVIEWS_MIN: 'pageviews_min',
                PAGEVIEWS_MAX: 'pageviews_max',
                CONCURRENCY: 'concurrency',
                PAUSE_BETWEEN_PVS_MIN: 'pause_between_pvs_min',
                PAUSE_BETWEEN_PVS_MAX: 'pause_between_pvs_max',
                AUTO_STOP_AFTER_HOURS: 'auto_stop_after_hours',
                MAX_TOTAL_VISITS: 'max_total_visits',
                SITESEARCH_PROBABILITY: 'sitesearch_probability',
                OUTLINKS_PROBABILITY: 'outlinks_probability',
                DOWNLOADS_PROBABILITY: 'downloads_probability',
                CLICK_EVENTS_PROBABILITY: 'click_events_probability',
                RANDOM_EVENTS_PROBABILITY: 'random_events_probability',
                DIRECT_TRAFFIC_PROBABILITY: 'direct_traffic_probability',
                ECOMMERCE_PROBABILITY: 'ecommerce_probability',
                VISIT_DURATION_MIN: 'visit_duration_min',
                VISIT_DURATION_MAX: 'visit_duration_max',
                RANDOMIZE_VISITOR_COUNTRIES: 'randomize_visitor_countries',
                ECOMMERCE_ORDER_VALUE_MIN: 'ecommerce_order_value_min',
                ECOMMERCE_ORDER_VALUE_MAX: 'ecommerce_order_value_max',
                ECOMMERCE_CURRENCY: 'ecommerce_currency',
                TIMEZONE: 'timezone',
            };

            const presetKey = map[key];
            if (presetKey && Object.prototype.hasOwnProperty.call(presetConfig, presetKey)) {
                const value = presetConfig[presetKey];
                if (value !== undefined && value !== null && value !== '') {
                    return value;
                }
            }
        }

        return defaultValue;
    }

    // Format configuration value for display
    formatConfigValue(key, value) {
        if (value === null || value === undefined) {
            return '--';
        }
        if (key === 'TARGET_VISITS_PER_DAY') {
            const num = Number(value);
            return Number.isNaN(num) ? value : num.toLocaleString();
        }
        if (key.includes('PROBABILITY')) {
            const num = typeof value === 'number' ? value : parseFloat(value);
            if (Number.isNaN(num)) {
                return value;
            }
            return `${(num * 100).toFixed(0)}%`;
        }
        if (key === 'RANDOMIZE_VISITOR_COUNTRIES') {
            if (typeof value === 'boolean') {
                return value ? 'Enabled' : 'Disabled';
            }
            return value === 'true' || value === '1' ? 'Enabled' : 'Disabled';
        }
        return typeof value === 'string' ? value : String(value);
    }

    // Backfill summary panel
    updateBackfill(status) {
        const container = document.getElementById('backfill-status');
        if (!container) return;

        const enabledRaw = this.getConfigValue(status, 'BACKFILL_ENABLED', 'false');
        const enabled = String(enabledRaw).toLowerCase() === 'true' || String(enabledRaw) === '1';

        if (!enabled) {
            container.innerHTML = `<p class="text-sm text-gray-500">Backfill is disabled.</p>`;
            return;
        }

        const start = this.getConfigValue(status, 'BACKFILL_START_DATE', null);
        const end = this.getConfigValue(status, 'BACKFILL_END_DATE', null);
        const daysBack = this.getConfigValue(status, 'BACKFILL_DAYS_BACK', null);
        const duration = this.getConfigValue(status, 'BACKFILL_DURATION_DAYS', null);
        const perDay = this.getConfigValue(status, 'BACKFILL_MAX_VISITS_PER_DAY', null);
        const total = this.getConfigValue(status, 'BACKFILL_MAX_VISITS_TOTAL', null);
        const rps = this.getConfigValue(status, 'BACKFILL_RPS_LIMIT', null);
        const seed = this.getConfigValue(status, 'BACKFILL_SEED', null);

        const windowText = (() => {
            if (start && end) {
                return `Absolute: ${start} → ${end}`;
            }
            if (daysBack && duration) {
                return `Relative: ${daysBack} days back for ${duration} day(s)`;
            }
            return 'Window not fully specified';
        })();

        const capsText = `Caps: ${perDay || '—'} /day, total ${total || '—'}`;
        const throttleText = rps ? `Throttle: ${rps} rps` : 'Throttle: default';
        const seedText = seed || seed === 0 ? `Seed: ${seed}` : 'Seed: not set';

        container.innerHTML = `
            <div class="flex items-center gap-2">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700">Backfill Enabled</span>
            </div>
            <p class="text-sm text-gray-700">${windowText}</p>
            <p class="text-sm text-gray-700">${capsText}</p>
            <p class="text-sm text-gray-700">${throttleText}</p>
            <p class="text-sm text-gray-700">${seedText}</p>
            <p class="text-xs text-gray-400">Dates and caps are validated on apply; check logs for per-day summaries.</p>
        `;
    }

    // Show error state
    showError(message) {
        const statusText = document.getElementById('status-text');
        const statusSubtitle = document.getElementById('status-subtitle');
        
        if (statusText) {
            statusText.textContent = 'Error';
            statusText.className = 'text-2xl font-bold text-red-600';
        }
        
        if (statusSubtitle) {
            statusSubtitle.textContent = message;
        }
        
        // Hide all control buttons on error
        const buttons = ['start-btn', 'stop-btn', 'restart-btn'];
        buttons.forEach(id => {
            const btn = document.getElementById(id);
            if (btn) btn.classList.add('hidden');
        });
    }

    // Handle start button
    async handleStart() {
        UI.confirm(
            'Start the load generator? This will begin sending traffic to your Matomo instance.',
            async () => {
                try {
                    UI.showLoading('Starting container...');
                    const result = await api.startContainer();
                    UI.hideLoading();
                    
                    if (result.status === 'started' || result.status === 'running') {
                        UI.showAlert('✅ Container started successfully!', 'success');
                        await this.loadStatus();
                        await this.refreshSavedPresets();
                    } else {
                        UI.showAlert(`Container started with status: ${result.status}`, 'warning');
                        await this.loadStatus();
                        await this.refreshSavedPresets();
                    }
                } catch (error) {
                    UI.hideLoading();
                    UI.showAlert(`Failed to start container: ${error.message}`, 'error');
                }
            }
        );
    }

    // Handle stop button
    async handleStop() {
        UI.confirm(
            'Stop the load generator? This will halt all traffic generation.',
            async () => {
                try {
                    UI.showLoading('Stopping container...');
                    const result = await api.stopContainer(10);
                    UI.hideLoading();
                    
                    if (result.status === 'stopped') {
                        UI.showAlert('✅ Container stopped successfully!', 'success');
                        await this.loadStatus();
                        await this.refreshSavedPresets();
                    } else {
                        UI.showAlert(`Container stopped with status: ${result.status}`, 'warning');
                        await this.loadStatus();
                        await this.refreshSavedPresets();
                    }
                } catch (error) {
                    UI.hideLoading();
                    UI.showAlert(`Failed to stop container: ${error.message}`, 'error');
                }
            }
        );
    }

    // Handle restart button
    async handleRestart() {
        UI.confirm(
            'Restart the load generator? This will stop and start the container with current configuration.',
            async () => {
                try {
                    UI.showLoading('Restarting container...');
                    const result = await api.restartContainer(10);
                    UI.hideLoading();
                    
                    if (result.status === 'running') {
                        UI.showAlert('✅ Container restarted successfully!', 'success');
                        await this.loadStatus();
                        await this.refreshSavedPresets();
                    } else {
                        UI.showAlert(`Container restarted with status: ${result.status}`, 'warning');
                        await this.loadStatus();
                        await this.refreshSavedPresets();
                    }
                } catch (error) {
                    UI.hideLoading();
                    UI.showAlert(`Failed to restart container: ${error.message}`, 'error');
                }
            }
        );
    }

    // Start auto-refresh
    startAutoRefresh() {
        // Clear any existing interval
        this.stopAutoRefresh();
        
        // Refresh every 5 seconds
        this.refreshInterval = setInterval(() => {
            this.loadStatus();
        }, 5000);
    }

    // Stop auto-refresh
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
}

// Export for use in app
window.StatusDashboard = StatusDashboard;
