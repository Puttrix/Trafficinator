// Configuration Form Management
class ConfigForm {
    constructor() {
        this.form = null;
        this.currentConfig = null;
        this.validationErrors = {};
    }

    // Initialize the configuration form
    init() {
        this.form = document.getElementById('config-form');
        if (!this.form) return;

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
    }

    // Load current configuration from API
    async loadCurrentConfig() {
        try {
            UI.showLoading('Loading configuration...');
            const status = await api.getStatus();
            
            // Parse environment variables if container is running
            if (status.status === 'running' && status.environment) {
                this.currentConfig = this.parseEnvVars(status.environment);
                this.populateForm(this.currentConfig);
            }
            
            UI.hideLoading();
        } catch (error) {
            UI.hideLoading();
            console.error('Failed to load config:', error);
            UI.showAlert('Could not load current configuration. Form will show defaults.', 'warning');
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
        
        return config;
    }

    // Populate form with config values
    populateForm(config) {
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

    // Validate single field
    validateField(input) {
        const name = input.name;
        const value = input.value;
        let error = null;
        
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
        
        // Get configuration
        const config = this.getFormData();
        
        // For now, just show success message
        // P-018 will implement actual persistence
        UI.showAlert('Configuration validated successfully. Start the container to apply.', 'info');
        console.log('Configuration:', config);
        
        // TODO: Implement save to backend when P-018 is complete
    }
}

// Initialize configuration form when tab is shown
window.ConfigForm = ConfigForm;
