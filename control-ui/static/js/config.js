// Configuration Form Management
class ConfigForm {
    constructor() {
        this.form = null;
        this.currentConfig = null;
        this.validationErrors = {};
        this.multiTargetManager = null;
    }

    // Initialize the configuration form
    init() {
        this.form = document.getElementById('config-form');
        if (!this.form) return;

        // Initialize multi-target manager (P-008)
        if (window.MultiTargetManager) {
            this.multiTargetManager = new window.MultiTargetManager();
            this.multiTargetManager.init();
        }

        this.setupEventListeners();
        this.loadCurrentConfig();
    }

    // Setup event listeners
    setupEventListeners() {
        // Form submission
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSave();
        });

        // Test connection button
        const testBtn = document.getElementById('test-connection-btn');
        if (testBtn) {
            testBtn.addEventListener('click', () => this.testConnection());
        }

        // Validate button
        const validateBtn = document.getElementById('validate-config-btn');
        if (validateBtn) {
            validateBtn.addEventListener('click', () => this.validateConfig());
        }

        // Real-time validation on blur
        const inputs = this.form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', () => this.validateField(input));
            input.addEventListener('input', () => this.clearFieldError(input));
        });

        // Feature toggle listeners
        const toggles = this.form.querySelectorAll('[data-toggle-group]');
        toggles.forEach(toggle => {
            toggle.addEventListener('change', () => this.handleToggle(toggle));
        });

        // Save as preset button
        const savePresetBtn = document.getElementById('save-as-preset-btn');
        if (savePresetBtn) {
            savePresetBtn.addEventListener('click', () => this.saveAsPreset());
        }
    }

    // Load current configuration from API
    async loadCurrentConfig() {
        try {
            UI.showLoading('Loading configuration...');
            const status = await api.getStatus();
            let configLoaded = false;

            if (status?.config) {
                const envList = Object.entries(status.config)
                    .filter(([, value]) => value !== undefined && value !== null)
                    .map(([key, value]) => `${key}=${value}`);
                
                if (envList.length > 0) {
                    const parsedConfig = this.parseEnvVars(envList);
                    if (Object.keys(parsedConfig).length > 0) {
                        this.currentConfig = parsedConfig;
                        this.populateForm(parsedConfig);
                        configLoaded = true;
                    }
                }
            }

            if (!configLoaded) {
                const latestPreset = await this.fetchLatestPresetConfig();
                if (latestPreset) {
                    this.currentConfig = latestPreset;
                    this.populateForm(latestPreset);
                    UI.showAlert('Loaded your most recent saved preset into the form.', 'info', 4000);
                    configLoaded = true;
                }
            }

            if (!configLoaded) {
                console.info('No active container configuration or saved presets found; using default form values.');
            }
        } catch (error) {
            console.error('Failed to load config:', error);
            UI.showAlert('Could not load current configuration. Form will show defaults.', 'warning');
        } finally {
            UI.hideLoading();
        }
    }

    async fetchLatestPresetConfig() {
        try {
            const response = await api.request('/api/presets');
            const presets = response.presets || [];
            if (presets.length === 0) {
                return null;
            }

            const latest = presets[0];
            const detail = await api.request(`/api/presets/${latest.id}`);
            return detail.config || null;
        } catch (error) {
            console.error('Failed to load latest preset configuration:', error);
            return null;
        }
    }

    // Parse environment variables into config object
    parseEnvVars(envVars) {
        const config = {};
        
        envVars.forEach(envVar => {
            const [key, value] = envVar.split('=');
            
            // Map env vars to config keys
            switch(key) {
                case 'MATOMO_URL':
                    config.matomo_url = value;
                    break;
                case 'MATOMO_SITE_ID':
                    config.matomo_site_id = parseInt(value);
                    break;
                case 'MATOMO_TOKEN_AUTH':
                    config.matomo_token_auth = value;
                    break;
                case 'TARGET_VISITS_PER_DAY':
                    config.target_visits_per_day = parseFloat(value);
                    break;
                case 'PAGEVIEWS_MIN':
                    config.pageviews_min = parseInt(value);
                    break;
                case 'PAGEVIEWS_MAX':
                    config.pageviews_max = parseInt(value);
                    break;
                case 'CONCURRENCY':
                    config.concurrency = parseInt(value);
                    break;
                case 'PAUSE_BETWEEN_PVS_MIN':
                    config.pause_between_pvs_min = parseFloat(value);
                    break;
                case 'PAUSE_BETWEEN_PVS_MAX':
                    config.pause_between_pvs_max = parseFloat(value);
                    break;
                case 'AUTO_STOP_AFTER_HOURS':
                    config.auto_stop_after_hours = parseFloat(value);
                    break;
                case 'MAX_TOTAL_VISITS':
                    config.max_total_visits = parseInt(value);
                    break;
                case 'SITESEARCH_PROBABILITY':
                    config.sitesearch_probability = parseFloat(value);
                    break;
                case 'OUTLINKS_PROBABILITY':
                    config.outlinks_probability = parseFloat(value);
                    break;
                case 'DOWNLOADS_PROBABILITY':
                    config.downloads_probability = parseFloat(value);
                    break;
                case 'CLICK_EVENTS_PROBABILITY':
                    config.click_events_probability = parseFloat(value);
                    break;
                case 'RANDOM_EVENTS_PROBABILITY':
                    config.random_events_probability = parseFloat(value);
                    break;
                case 'DIRECT_TRAFFIC_PROBABILITY':
                    config.direct_traffic_probability = parseFloat(value);
                    break;
                case 'ECOMMERCE_PROBABILITY':
                    config.ecommerce_probability = parseFloat(value);
                    break;
                case 'VISIT_DURATION_MIN':
                    config.visit_duration_min = parseFloat(value);
                    break;
                case 'VISIT_DURATION_MAX':
                    config.visit_duration_max = parseFloat(value);
                    break;
                case 'RANDOMIZE_VISITOR_COUNTRIES':
                    config.randomize_visitor_countries = value === 'true' || value === '1';
                    break;
                case 'ECOMMERCE_ORDER_VALUE_MIN':
                    config.ecommerce_order_value_min = parseFloat(value);
                    break;
                case 'ECOMMERCE_ORDER_VALUE_MAX':
                    config.ecommerce_order_value_max = parseFloat(value);
                    break;
                case 'ECOMMERCE_CURRENCY':
                    config.ecommerce_currency = value;
                    break;
                case 'TIMEZONE':
                    config.timezone = value;
                    break;
            }
        });

        if (config.matomo_token_auth === '***MASKED***') {
            config.matomo_token_auth = '';
        }
        
        return config;
    }

    // Populate form with config values
    populateForm(config) {
        // Check if this is a multi-target config (P-008)
        if (config.targets && Array.isArray(config.targets) && config.targets.length > 0) {
            if (this.multiTargetManager) {
                this.multiTargetManager.loadMultiTargetConfig(config);
            }
            return;
        }

        for (const [key, value] of Object.entries(config)) {
            const input = this.form.querySelector(`[name="${key}"]`);
            if (input) {
                if (input.type === 'checkbox') {
                    input.checked = value === true || value === 'true' || value === '1';
                } else {
                    input.value = value;
                }
                
                // Trigger toggle handlers
                if (input.dataset.toggleGroup) {
                    this.handleToggle(input);
                }
            }
        }
    }

    // Get form data as config object
    getFormData() {
        // Check if multi-target mode is active (P-008)
        if (this.multiTargetManager && this.multiTargetManager.isMultiTargetMode) {
            const multiTargetConfig = this.multiTargetManager.getMultiTargetConfig();
            if (multiTargetConfig) {
                // Merge multi-target config with other form fields
                const formData = new FormData(this.form);
                const config = { ...multiTargetConfig };
                
                // Include non-target fields
                for (const [key, value] of formData.entries()) {
                    // Skip single-target fields and distribution_strategy (already in multiTargetConfig)
                    if (['matomo_url', 'matomo_site_id', 'matomo_token_auth', 'distribution_strategy'].includes(key)) {
                        continue;
                    }
                    
                    const input = this.form.querySelector(`[name="${key}"]`);
                    if (!input) continue;
                    
                    if (input.type === 'number') {
                        const num = parseFloat(value);
                        config[key] = isNaN(num) ? 0 : num;
                    } else if (input.type === 'checkbox') {
                        config[key] = input.checked;
                    } else {
                        config[key] = value.trim();
                    }
                }
                
                return config;
            }
        }

        // Single-target mode (legacy)
        const formData = new FormData(this.form);
        const config = {};
        
        for (const [key, value] of formData.entries()) {
            const input = this.form.querySelector(`[name="${key}"]`);
            
            if (input.type === 'number') {
                const num = parseFloat(value);
                config[key] = isNaN(num) ? 0 : num;
            } else if (input.type === 'checkbox') {
                config[key] = input.checked;
            } else {
                // Only include the value if it's not empty
                // Empty strings can fail backend validation
                config[key] = value.trim();
            }
        }
        
        return config;
    }

    // Validate entire configuration
    async validateConfig() {
        // Client-side validation for multi-target mode
        if (this.multiTargetManager && this.multiTargetManager.isMultiTargetMode) {
            const clientErrors = this.validateMultiTargetConfig();
            if (clientErrors.length > 0) {
                clientErrors.forEach(error => {
                    UI.showAlert(error, 'error');
                });
                return false;
            }
        }

        const config = this.getFormData();
        
        try {
            UI.showLoading('Validating configuration...');
            const result = await api.validateConfig(config);
            UI.hideLoading();
            
            // Clear previous errors
            this.validationErrors = {};
            this.clearAllErrors();
            
            // Display errors
            if (result.errors && result.errors.length > 0) {
                result.errors.forEach(error => {
                    this.showFieldError(error.field, error.message);
                    this.validationErrors[error.field] = error.message;
                });
                UI.showAlert(`Configuration has ${result.errors.length} error(s)`, 'error');
            }
            
            // Display warnings
            if (result.warnings && result.warnings.length > 0) {
                result.warnings.forEach(warning => {
                    this.showFieldWarning(warning.field, warning.message);
                });
                UI.showAlert(`Configuration has ${result.warnings.length} warning(s)`, 'warning');
            }
            
            // Success message
            if (result.valid && result.errors.length === 0) {
                UI.showAlert('Configuration is valid!', 'success');
            }
            
            return result.valid;
            
        } catch (error) {
            UI.hideLoading();
            UI.showAlert(`Validation failed: ${error.message}`, 'error');
            return false;
        }
    }

    // Validate multi-target configuration (client-side)
    validateMultiTargetConfig() {
        const errors = [];
        
        if (!this.multiTargetManager || !this.multiTargetManager.targets || this.multiTargetManager.targets.length === 0) {
            errors.push('At least one target is required in multi-target mode');
            return errors;
        }

        const enabledTargets = this.multiTargetManager.targets.filter(t => t.enabled);
        if (enabledTargets.length === 0) {
            errors.push('At least one target must be enabled');
            return errors;
        }

        // Validate each target
        this.multiTargetManager.targets.forEach((target, index) => {
            if (!target.name || target.name.trim() === '') {
                errors.push(`Target ${index + 1}: Name is required`);
            }
            if (!target.url || target.url.trim() === '') {
                errors.push(`Target ${index + 1}: URL is required`);
            } else {
                try {
                    const url = new URL(target.url);
                    if (!['http:', 'https:'].includes(url.protocol)) {
                        errors.push(`Target ${index + 1}: URL must use http:// or https://`);
                    }
                } catch {
                    errors.push(`Target ${index + 1}: Invalid URL format`);
                }
            }
            if (!target.site_id || target.site_id < 1) {
                errors.push(`Target ${index + 1}: Site ID must be at least 1`);
            }
        });

        // Check for duplicate names
        const names = this.multiTargetManager.targets.map(t => t.name.trim().toLowerCase());
        const duplicates = names.filter((name, index) => names.indexOf(name) !== index);
        if (duplicates.length > 0) {
            errors.push('Target names must be unique');
        }

        return errors;
    }

    // Validate single field
    validateField(input) {
        const name = input.name;
        const value = input.value;
        let error = null;
        
        // Skip validation of single-target fields when in multi-target mode
        if (this.multiTargetManager && this.multiTargetManager.isMultiTargetMode) {
            if (['matomo_url', 'matomo_site_id', 'matomo_token_auth'].includes(name)) {
                return true; // Skip validation for hidden single-target fields
            }
        }
        
        // Required fields
        if (input.hasAttribute('required') && (!value || value.trim() === '')) {
            error = 'This field is required';
        }
        
        // Number validation
        if (input.type === 'number' && value) {
            const num = parseFloat(value);
            const min = parseFloat(input.getAttribute('min'));
            const max = parseFloat(input.getAttribute('max'));
            
            if (isNaN(num)) {
                error = 'Must be a valid number';
            } else if (!isNaN(min) && num < min) {
                error = `Must be at least ${min}`;
            } else if (!isNaN(max) && num > max) {
                error = `Must be at most ${max}`;
            }
        }
        
        // URL validation
        if (name === 'matomo_url' && value) {
            try {
                const url = new URL(value);
                if (!['http:', 'https:'].includes(url.protocol)) {
                    error = 'URL must use http:// or https://';
                }
            } catch {
                error = 'Invalid URL format';
            }
        }
        
        // Currency validation
        if (name === 'ecommerce_currency' && value) {
            if (!/^[A-Z]{3}$/.test(value)) {
                error = 'Currency must be 3 uppercase letters (e.g., USD, EUR, GBP)';
            }
        }
        
        // Range validations
        if (name.endsWith('_min')) {
            const maxField = name.replace('_min', '_max');
            const maxInput = this.form.querySelector(`[name="${maxField}"]`);
            if (maxInput) {
                const minVal = parseFloat(value);
                const maxVal = parseFloat(maxInput.value);
                if (!isNaN(minVal) && !isNaN(maxVal) && minVal > maxVal) {
                    error = `Minimum cannot be greater than maximum (${maxVal})`;
                }
            }
        }
        
        if (error) {
            this.showFieldError(name, error);
        } else {
            this.clearFieldError(input);
        }
        
        return !error;
    }

    // Show field error
    showFieldError(fieldName, message) {
        const input = this.form.querySelector(`[name="${fieldName}"]`);
        if (!input) return;
        
        const formGroup = input.closest('.form-group');
        if (!formGroup) return;
        
        // Add error class
        input.classList.add('border-red-500', 'focus:ring-red-500');
        input.classList.remove('border-gray-300', 'focus:ring-primary');
        
        // Remove existing error message
        const existingError = formGroup.querySelector('.field-error');
        if (existingError) existingError.remove();
        
        // Add error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error text-sm text-red-600 mt-1';
        errorDiv.textContent = message;
        input.parentNode.appendChild(errorDiv);
    }

    // Show field warning
    showFieldWarning(fieldName, message) {
        const input = this.form.querySelector(`[name="${fieldName}"]`);
        if (!input) return;
        
        const formGroup = input.closest('.form-group');
        if (!formGroup) return;
        
        // Add warning class
        input.classList.add('border-yellow-500');
        
        // Remove existing warning
        const existingWarning = formGroup.querySelector('.field-warning');
        if (existingWarning) existingWarning.remove();
        
        // Add warning message
        const warningDiv = document.createElement('div');
        warningDiv.className = 'field-warning text-sm text-yellow-600 mt-1';
        warningDiv.textContent = message;
        input.parentNode.appendChild(warningDiv);
    }

    // Clear field error
    clearFieldError(input) {
        input.classList.remove('border-red-500', 'focus:ring-red-500', 'border-yellow-500');
        input.classList.add('border-gray-300', 'focus:ring-primary');
        
        const formGroup = input.closest('.form-group');
        if (!formGroup) return;
        
        const error = formGroup.querySelector('.field-error');
        if (error) error.remove();
        
        const warning = formGroup.querySelector('.field-warning');
        if (warning) warning.remove();
    }

    // Clear all errors
    clearAllErrors() {
        const inputs = this.form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => this.clearFieldError(input));
    }

    // Handle feature toggles
    handleToggle(toggle) {
        const groupName = toggle.dataset.toggleGroup;
        const group = this.form.querySelector(`[data-toggle-target="${groupName}"]`);
        
        if (group) {
            if (toggle.checked) {
                group.classList.remove('hidden');
            } else {
                group.classList.add('hidden');
            }
        }
    }

    // Test Matomo connection
    async testConnection() {
        // In multi-target mode, use "Test All Targets" instead
        if (this.multiTargetManager && this.multiTargetManager.isMultiTargetMode) {
            UI.showAlert('In multi-target mode, use "Test All Targets" button instead', 'info');
            return;
        }

        const matomoUrl = this.form.querySelector('[name="matomo_url"]').value;
        const siteId = this.form.querySelector('[name="matomo_site_id"]').value;
        
        if (!matomoUrl || !siteId) {
            UI.showAlert('Please enter Matomo URL and Site ID first', 'warning');
            return;
        }
        
        try {
            UI.showLoading('Testing Matomo connection...');
            const result = await api.testConnection(matomoUrl, parseInt(siteId));
            UI.hideLoading();
            
            if (result.success) {
                UI.showAlert(`✅ Connection successful! Response time: ${result.response_time_ms}ms`, 'success');
            } else {
                UI.showAlert(`❌ Connection failed: ${result.error || result.message}`, 'error');
            }
            
        } catch (error) {
            UI.hideLoading();
            UI.showAlert(`Connection test failed: ${error.message}`, 'error');
        }
    }

    // Handle form save
    async handleSave() {
        // First validate
        const isValid = await this.validateConfig();
        
        if (!isValid) {
            UI.showAlert('Please fix validation errors before saving', 'error');
            return;
        }
        
        // Confirm with user
        const confirmed = confirm(
            'This will apply the new configuration and restart the container.\n\n' +
            'Any running load generation will be interrupted.\n\n' +
            'Continue?'
        );
        
        if (!confirmed) {
            return;
        }
        
        try {
            // Get configuration
            const config = this.getFormData();
            
            UI.showLoading('Applying configuration...');
            
            // Apply configuration to container
            const result = await api.applyConfig(config);
            
            UI.hideLoading();
            
            if (result.success) {
                UI.showAlert(result.message, 'success');
                
                // Reload the page to refresh status
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            } else {
                UI.showAlert(`Failed to apply configuration: ${result.error || result.message}`, 'error');
            }
            
        } catch (error) {
            UI.hideLoading();
            UI.showAlert(`Error applying configuration: ${error.message}`, 'error');
            console.error('Apply config error:', error);
        }
    }

    // Save current configuration as a preset
    async saveAsPreset() {
        // First validate
        const isValid = await this.validateConfig();
        
        if (!isValid) {
            UI.showAlert('Please fix validation errors before saving as preset', 'error');
            return;
        }

        // Create a custom dialog for preset name and description
        const dialogHtml = `
            <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" id="save-preset-dialog">
                <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                    <h3 class="text-lg font-semibold mb-4">Save Configuration as Preset</h3>
                    <div class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Preset Name *</label>
                            <input type="text" id="preset-name-input" 
                                   class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                   placeholder="e.g., Production Load Test">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Description (optional)</label>
                            <textarea id="preset-description-input" rows="3"
                                      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                      placeholder="Describe this configuration..."></textarea>
                        </div>
                    </div>
                    <div class="flex justify-end gap-3 mt-6">
                        <button id="cancel-preset-btn" class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
                            Cancel
                        </button>
                        <button id="save-preset-confirm-btn" class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700">
                            Save Preset
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Add dialog to DOM
        document.body.insertAdjacentHTML('beforeend', dialogHtml);
        
        const dialog = document.getElementById('save-preset-dialog');
        const nameInput = document.getElementById('preset-name-input');
        const descInput = document.getElementById('preset-description-input');
        const cancelBtn = document.getElementById('cancel-preset-btn');
        const saveBtn = document.getElementById('save-preset-confirm-btn');

        // Focus name input
        nameInput.focus();

        // Cancel handler
        const closeDialog = () => {
            dialog.remove();
        };

        cancelBtn.addEventListener('click', closeDialog);
        dialog.addEventListener('click', (e) => {
            if (e.target === dialog) closeDialog();
        });

        // Save handler
        saveBtn.addEventListener('click', async () => {
            const name = nameInput.value.trim();
            
            if (!name) {
                UI.showAlert('Please enter a preset name', 'error');
                nameInput.focus();
                return;
            }

            const description = descInput.value.trim() || null;

            try {
                closeDialog();
                UI.showLoading('Saving preset...');
                
                // Get the presets manager (from the global instance)
                if (!window.loadPresets) {
                    throw new Error('Presets manager not initialized');
                }

                await window.loadPresets.saveCustomPreset(name, description);
                
                UI.hideLoading();

                // Offer to switch to presets tab
                UI.confirm(
                    'Preset saved successfully! Would you like to view your saved presets?',
                    () => {
                        UI.switchTab('presets');
                    }
                );
                
            } catch (error) {
                UI.hideLoading();
                UI.showAlert(`Error saving preset: ${error.message}`, 'error');
                console.error('Save preset error:', error);
            }
        });

        // Enter key to save
        nameInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                saveBtn.click();
            }
        });
    }
}

// Initialize configuration form when tab is shown
window.ConfigForm = ConfigForm;
