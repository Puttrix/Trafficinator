// Load Presets Management
class LoadPresets {
    constructor() {
        this.presets = {
            light: {
                name: "Light Load",
                description: "Low-volume testing - ideal for development and testing",
                icon: "🌤️",
                color: "blue",
                config: {
                    matomo_url: "",  // Keep user's existing URL
                    matomo_site_id: null,  // Keep user's existing site ID
                    matomo_token_auth: null,  // Keep user's existing token
                    target_visits_per_day: 1000,
                    pageviews_min: 2,
                    pageviews_max: 4,
                    concurrency: 10,
                    pause_between_pvs_min: 1.0,
                    pause_between_pvs_max: 3.0,
                    auto_stop_after_hours: 0,
                    max_total_visits: 0,
                    sitesearch_probability: 0.10,
                    outlinks_probability: 0.05,
                    downloads_probability: 0.03,
                    click_events_probability: 0.15,
                    random_events_probability: 0.08,
                    direct_traffic_probability: 0.40,
                    ecommerce_probability: 0.02,
                    visit_duration_min: 0.5,
                    visit_duration_max: 3.0,
                    randomize_visitor_countries: false,
                    ecommerce_order_value_min: 15.99,
                    ecommerce_order_value_max: 99.99,
                    ecommerce_currency: "SEK",
                    timezone: "CET"
                },
                metrics: {
                    visitsPerDay: "1,000",
                    visitsPerHour: "~42",
                    concurrency: "10",
                    pageviews: "2-4"
                }
            },
            medium: {
                name: "Medium Load",
                description: "Moderate traffic - realistic production simulation",
                icon: "☀️",
                color: "green",
                config: {
                    matomo_url: "",
                    matomo_site_id: null,
                    matomo_token_auth: null,
                    target_visits_per_day: 10000,
                    pageviews_min: 3,
                    pageviews_max: 6,
                    concurrency: 50,
                    pause_between_pvs_min: 0.5,
                    pause_between_pvs_max: 2.0,
                    auto_stop_after_hours: 0,
                    max_total_visits: 0,
                    sitesearch_probability: 0.15,
                    outlinks_probability: 0.10,
                    downloads_probability: 0.08,
                    click_events_probability: 0.25,
                    random_events_probability: 0.12,
                    direct_traffic_probability: 0.30,
                    ecommerce_probability: 0.05,
                    visit_duration_min: 1.0,
                    visit_duration_max: 8.0,
                    randomize_visitor_countries: true,
                    ecommerce_order_value_min: 15.99,
                    ecommerce_order_value_max: 299.99,
                    ecommerce_currency: "SEK",
                    timezone: "CET"
                },
                metrics: {
                    visitsPerDay: "10,000",
                    visitsPerHour: "~417",
                    concurrency: "50",
                    pageviews: "3-6"
                }
            },
            heavy: {
                name: "Heavy Load",
                description: "High-volume stress testing - maximum throughput",
                icon: "🔥",
                color: "orange",
                config: {
                    matomo_url: "",
                    matomo_site_id: null,
                    matomo_token_auth: null,
                    target_visits_per_day: 50000,
                    pageviews_min: 4,
                    pageviews_max: 8,
                    concurrency: 150,
                    pause_between_pvs_min: 0.3,
                    pause_between_pvs_max: 1.5,
                    auto_stop_after_hours: 0,
                    max_total_visits: 0,
                    sitesearch_probability: 0.20,
                    outlinks_probability: 0.15,
                    downloads_probability: 0.12,
                    click_events_probability: 0.30,
                    random_events_probability: 0.15,
                    direct_traffic_probability: 0.25,
                    ecommerce_probability: 0.08,
                    visit_duration_min: 2.0,
                    visit_duration_max: 12.0,
                    randomize_visitor_countries: true,
                    ecommerce_order_value_min: 15.99,
                    ecommerce_order_value_max: 499.99,
                    ecommerce_currency: "SEK",
                    timezone: "CET"
                },
                metrics: {
                    visitsPerDay: "50,000",
                    visitsPerHour: "~2,083",
                    concurrency: "150",
                    pageviews: "4-8"
                }
            },
            extreme: {
                name: "Extreme Load",
                description: "Maximum stress - enterprise scale testing",
                icon: "⚡",
                color: "red",
                config: {
                    matomo_url: "",
                    matomo_site_id: null,
                    matomo_token_auth: null,
                    target_visits_per_day: 100000,
                    pageviews_min: 5,
                    pageviews_max: 10,
                    concurrency: 300,
                    pause_between_pvs_min: 0.2,
                    pause_between_pvs_max: 1.0,
                    auto_stop_after_hours: 0,
                    max_total_visits: 0,
                    sitesearch_probability: 0.25,
                    outlinks_probability: 0.18,
                    downloads_probability: 0.15,
                    click_events_probability: 0.35,
                    random_events_probability: 0.18,
                    direct_traffic_probability: 0.20,
                    ecommerce_probability: 0.10,
                    visit_duration_min: 3.0,
                    visit_duration_max: 15.0,
                    randomize_visitor_countries: true,
                    ecommerce_order_value_min: 15.99,
                    ecommerce_order_value_max: 999.99,
                    ecommerce_currency: "SEK",
                    timezone: "CET"
                },
                metrics: {
                    visitsPerDay: "100,000",
                    visitsPerHour: "~4,167",
                    concurrency: "300",
                    pageviews: "5-10"
                }
            }
        };
        
        this.activePreset = null;
    }

    // Initialize presets
    init() {
        this.renderPresets();
        this.setupEventListeners();
    }

    // Render preset cards
    renderPresets() {
        const container = document.getElementById('presets-container');
        if (!container) return;

        let html = '';
        
        for (const [key, preset] of Object.entries(this.presets)) {
            const colorClasses = this.getColorClasses(preset.color);
            
            html += `
                <div class="preset-card bg-white rounded-lg shadow hover:shadow-lg transition-shadow cursor-pointer border-2 border-transparent" data-preset="${key}">
                    <div class="p-6">
                        <div class="flex items-start justify-between mb-4">
                            <div class="flex items-center gap-3">
                                <div class="text-4xl">${preset.icon}</div>
                                <div>
                                    <h3 class="text-lg font-semibold text-gray-900">${preset.name}</h3>
                                    <p class="text-sm text-gray-500 mt-1">${preset.description}</p>
                                </div>
                            </div>
                            <button class="load-preset-btn px-4 py-2 text-sm font-medium ${colorClasses.button} rounded-lg hover:opacity-90" data-preset="${key}">
                                Load
                            </button>
                        </div>
                        
                        <div class="grid grid-cols-2 gap-3 mt-4 pt-4 border-t border-gray-100">
                            <div>
                                <p class="text-xs text-gray-500">Visits/Day</p>
                                <p class="text-sm font-semibold text-gray-900">${preset.metrics.visitsPerDay}</p>
                            </div>
                            <div>
                                <p class="text-xs text-gray-500">Visits/Hour</p>
                                <p class="text-sm font-semibold text-gray-900">${preset.metrics.visitsPerHour}</p>
                            </div>
                            <div>
                                <p class="text-xs text-gray-500">Concurrency</p>
                                <p class="text-sm font-semibold text-gray-900">${preset.metrics.concurrency}</p>
                            </div>
                            <div>
                                <p class="text-xs text-gray-500">Pageviews</p>
                                <p class="text-sm font-semibold text-gray-900">${preset.metrics.pageviews}</p>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        container.innerHTML = html;
    }

    // Get color classes for preset
    getColorClasses(color) {
        const classes = {
            blue: {
                button: 'text-white bg-blue-600',
                border: 'border-blue-500'
            },
            green: {
                button: 'text-white bg-green-600',
                border: 'border-green-500'
            },
            orange: {
                button: 'text-white bg-orange-600',
                border: 'border-orange-500'
            },
            red: {
                button: 'text-white bg-red-600',
                border: 'border-red-500'
            }
        };
        
        return classes[color] || classes.blue;
    }

    // Setup event listeners
    setupEventListeners() {
        // Load preset buttons
        const loadButtons = document.querySelectorAll('.load-preset-btn');
        loadButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                const presetKey = button.dataset.preset;
                this.loadPreset(presetKey);
            });
        });

        // Preset card click
        const presetCards = document.querySelectorAll('.preset-card');
        presetCards.forEach(card => {
            card.addEventListener('click', () => {
                const presetKey = card.dataset.preset;
                this.selectPreset(presetKey);
            });
        });
    }

    // Select preset (visual indication)
    selectPreset(presetKey) {
        const preset = this.presets[presetKey];
        if (!preset) return;

        // Update active preset
        this.activePreset = presetKey;

        // Update visual indication
        const allCards = document.querySelectorAll('.preset-card');
        allCards.forEach(card => {
            card.classList.remove('border-blue-500', 'border-green-500', 'border-orange-500', 'border-red-500', 'bg-blue-50', 'bg-green-50', 'bg-orange-50', 'bg-red-50');
            card.classList.add('border-transparent');
        });

        const selectedCard = document.querySelector(`.preset-card[data-preset="${presetKey}"]`);
        if (selectedCard) {
            const colorClasses = this.getColorClasses(preset.color);
            selectedCard.classList.remove('border-transparent');
            selectedCard.classList.add(colorClasses.border);
        }
    }

    // Load preset into configuration form
    loadPreset(presetKey) {
        const preset = this.presets[presetKey];
        if (!preset) {
            UI.showAlert('Preset not found', 'error');
            return;
        }

        UI.confirm(
            `Load "${preset.name}" preset? This will replace current configuration values in the form.`,
            () => {
                try {
                    // Get current form values for URL, site ID, and token (don't overwrite these)
                    const currentMatomoUrl = document.querySelector('[name="matomo_url"]')?.value;
                    const currentSiteId = document.querySelector('[name="matomo_site_id"]')?.value;
                    const currentToken = document.querySelector('[name="matomo_token_auth"]')?.value;

                    // Merge preset config with current core values
                    const config = {
                        ...preset.config,
                        matomo_url: currentMatomoUrl || preset.config.matomo_url,
                        matomo_site_id: currentSiteId || preset.config.matomo_site_id,
                        matomo_token_auth: currentToken || preset.config.matomo_token_auth
                    };

                    // Load into form
                    this.populateForm(config);

                    // Select this preset visually
                    this.selectPreset(presetKey);

                    // Switch to config tab
                    UI.switchTab('config');

                    // Show success message
                    UI.showAlert(`✅ "${preset.name}" preset loaded successfully!`, 'success');

                } catch (error) {
                    console.error('Failed to load preset:', error);
                    UI.showAlert(`Failed to load preset: ${error.message}`, 'error');
                }
            }
        );
    }

    // Populate form with config
    populateForm(config) {
        const form = document.getElementById('config-form');
        if (!form) {
            throw new Error('Configuration form not found');
        }

        // Populate each field
        for (const [key, value] of Object.entries(config)) {
            const input = form.querySelector(`[name="${key}"]`);
            if (input) {
                if (input.type === 'checkbox') {
                    input.checked = value === true || value === 'true' || value === '1';
                    
                    // Trigger toggle handlers for conditional fields
                    if (input.dataset.toggleGroup) {
                        const event = new Event('change', { bubbles: true });
                        input.dispatchEvent(event);
                    }
                } else if (value !== null && value !== undefined) {
                    input.value = value;
                }

                // Clear any validation errors
                input.classList.remove('border-red-500', 'focus:ring-red-500');
                input.classList.add('border-gray-300', 'focus:ring-primary');
                
                const formGroup = input.closest('.form-group');
                if (formGroup) {
                    const error = formGroup.querySelector('.field-error');
                    if (error) error.remove();
                }
            }
        }
    }

    // Get active preset key
    getActivePreset() {
        return this.activePreset;
    }

    // Check if current form matches a preset
    detectPreset() {
        const form = document.getElementById('config-form');
        if (!form) return null;

        // Get current form values
        const currentConfig = {};
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            if (input.type === 'checkbox') {
                currentConfig[input.name] = input.checked;
            } else if (input.type === 'number') {
                currentConfig[input.name] = parseFloat(input.value);
            } else {
                currentConfig[input.name] = input.value;
            }
        });

        // Compare with presets (ignoring URL, site ID, token)
        for (const [key, preset] of Object.entries(this.presets)) {
            let matches = true;
            
            for (const [configKey, configValue] of Object.entries(preset.config)) {
                // Skip comparison for these fields
                if (['matomo_url', 'matomo_site_id', 'matomo_token_auth'].includes(configKey)) {
                    continue;
                }
                
                if (currentConfig[configKey] !== configValue) {
                    matches = false;
                    break;
                }
            }
            
            if (matches) {
                return key;
            }
        }
        
        return null;
    }

    // Load custom presets from database
    async loadCustomPresets() {
        try {
            const response = await api.request('/api/presets');
            return response.presets || [];
        } catch (error) {
            console.error('Failed to load custom presets:', error);
            return [];
        }
    }

    // Save current config as custom preset
    async saveCustomPreset(name, description = null) {
        const form = document.getElementById('config-form');
        if (!form) {
            throw new Error('Configuration form not found');
        }

        // Get current form config
        const config = {};
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            if (input.type === 'checkbox') {
                config[input.name] = input.checked;
            } else if (input.type === 'number') {
                config[input.name] = parseFloat(input.value) || 0;
            } else {
                config[input.name] = input.value.trim();
            }
        });

        try {
            const response = await api.request('/api/presets', {
                method: 'POST',
                body: JSON.stringify({ name, description, config })
            });
            
            await this.renderCustomPresets();
            if (window.app?.statusDashboard?.refreshSavedPresets) {
                window.app.statusDashboard.refreshSavedPresets();
            }

            UI.showAlert(`Preset "${name}" saved successfully!`, 'success');
            return response;
        } catch (error) {
            console.error('Failed to save preset:', error);
            throw error;
        }
    }

    // Load custom preset by ID
    async loadCustomPresetById(presetId) {
        try {
            const preset = await api.request(`/api/presets/${presetId}`);
            
            // Populate form with preset config
            this.populateForm(preset.config);
            
            UI.showAlert(`Preset "${preset.name}" loaded successfully!`, 'success');
            UI.switchTab('config');
            
            return preset;
        } catch (error) {
            console.error('Failed to load custom preset:', error);
            throw error;
        }
    }

    // Delete custom preset
    async deleteCustomPreset(presetId, presetName) {
        try {
            await api.request(`/api/presets/${presetId}`, {
                method: 'DELETE'
            });
            
            UI.showAlert(`Preset "${presetName}" deleted successfully!`, 'success');
        } catch (error) {
            console.error('Failed to delete preset:', error);
            throw error;
        }
    }

    // Render custom presets section
    async renderCustomPresets() {
        const container = document.getElementById('custom-presets-container');
        if (!container) return;

        const customPresets = await this.loadCustomPresets();

        if (customPresets.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <p class="text-sm">No custom presets saved yet.</p>
                    <p class="text-xs mt-1">Save your current configuration from the Config tab.</p>
                </div>
            `;
            return;
        }

        let html = '<div class="space-y-3">';
        
        customPresets.forEach(preset => {
            const createdDate = new Date(preset.created_at).toLocaleDateString();
            html += `
                <div class="flex items-center justify-between p-4 bg-white border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
                    <div class="flex-1">
                        <h4 class="font-medium text-gray-900">${UI.escapeHtml(preset.name)}</h4>
                        ${preset.description ? `<p class="text-sm text-gray-500 mt-1">${UI.escapeHtml(preset.description)}</p>` : ''}
                        <p class="text-xs text-gray-400 mt-1">Saved: ${createdDate}</p>
                    </div>
                    <div class="flex gap-2">
                        <button class="load-custom-preset-btn px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700" data-preset-id="${preset.id}" data-preset-name="${UI.escapeHtml(preset.name)}">
                            Load
                        </button>
                        <button class="delete-custom-preset-btn px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700" data-preset-id="${preset.id}" data-preset-name="${UI.escapeHtml(preset.name)}">
                            Delete
                        </button>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        container.innerHTML = html;

        // Add event listeners
        document.querySelectorAll('.load-custom-preset-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const presetId = parseInt(btn.dataset.presetId);
                const presetName = btn.dataset.presetName;
                
                UI.confirm(
                    `Load "${presetName}" preset?`,
                    async () => {
                        try {
                            await this.loadCustomPresetById(presetId);
                        } catch (error) {
                            UI.showAlert(`Failed to load preset: ${error.message}`, 'error');
                        }
                    }
                );
            });
        });

        document.querySelectorAll('.delete-custom-preset-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const presetId = parseInt(btn.dataset.presetId);
                const presetName = btn.dataset.presetName;
                
                UI.confirm(
                    `Delete "${presetName}" preset? This cannot be undone.`,
                    async () => {
                        try {
                            await this.deleteCustomPreset(presetId, presetName);
                            await this.renderCustomPresets();  // Refresh list
                            if (window.app?.statusDashboard?.refreshSavedPresets) {
                                window.app.statusDashboard.refreshSavedPresets();
                            }
                        } catch (error) {
                            UI.showAlert(`Failed to delete preset: ${error.message}`, 'error');
                        }
                    }
                );
            });
        });
    }
}

// Export for use in app
window.LoadPresets = LoadPresets;
