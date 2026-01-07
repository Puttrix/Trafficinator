// API Client for Matomo Load Generator Control UI
class API {
    constructor() {
        this.baseUrl = window.location.origin;
        this.apiKey = this.loadApiKey();
    }

    // Load API key from localStorage
    loadApiKey() {
        return localStorage.getItem('apiKey') || '';
    }

    // Save API key to localStorage
    saveApiKey(key) {
        this.apiKey = key;
        localStorage.setItem('apiKey', key);
    }

    // Clear API key
    clearApiKey() {
        this.apiKey = '';
        localStorage.removeItem('apiKey');
    }

    // Check if API key is set
    hasApiKey() {
        return this.apiKey && this.apiKey.length > 0;
    }

    // Get headers with auth
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json',
        };
        
        if (this.apiKey) {
            headers['X-API-Key'] = this.apiKey;
        }
        
        return headers;
    }

    // Generic request handler
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            ...options,
            headers: {
                ...this.getHeaders(),
                ...options.headers
            }
        };

        try {
            const response = await fetch(url, config);
            
            // Handle authentication errors
            if (response.status === 401 || response.status === 403) {
                throw new Error('Authentication failed. Please check your API key.');
            }

            // Handle rate limiting
            if (response.status === 429) {
                throw new Error('Rate limit exceeded. Please wait a moment and try again.');
            }

            // Parse JSON response
            const data = await response.json();
            
            // Handle error responses
            if (!response.ok) {
                throw new Error(data.detail || data.message || `HTTP ${response.status}: ${response.statusText}`);
            }

            return data;
        } catch (error) {
            // Network errors
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('Network error. Please check your connection and ensure the server is running.');
            }
            throw error;
        }
    }

    // Health check
    async health() {
        return this.request('/health');
    }

    // Get API info
    async info() {
        return this.request('/');
    }

    // Container Status
    async getStatus() {
        return this.request('/api/status');
    }

    // Start container
    async startContainer(config = null) {
        const options = { method: 'POST' };
        if (config && Object.keys(config).length > 0) {
            options.body = JSON.stringify({ config });
        }
        return this.request('/api/start', options);
    }

    // Stop container
    async stopContainer(timeout = 10) {
        const url = `/api/stop?timeout=${encodeURIComponent(timeout)}`;
        return this.request(url, { method: 'POST' });
    }

    // Restart container
    async restartContainer(timeout = 10) {
        const url = `/api/restart?timeout=${encodeURIComponent(timeout)}`;
        return this.request(url, { method: 'POST' });
    }

    // Get logs
    async getLogs(lines = 100) {
        return this.request(`/api/logs?lines=${lines}`);
    }

    // Validate configuration
    async validateConfig(config) {
        return this.request('/api/validate', {
            method: 'POST',
            body: JSON.stringify({ config })
        });
    }

    // Apply configuration to container
    async applyConfig(config) {
        return this.request('/api/config/apply', {
            method: 'POST',
            body: JSON.stringify({ config })
        });
    }

    // Test Matomo connection
    async testConnection(url, siteId, tokenAuth = '') {
        return this.request('/api/test-connection', {
            method: 'POST',
            body: JSON.stringify({
                matomo_url: url,
                site_id: siteId,
                token_auth: tokenAuth || undefined
            })
        });
    }

    // URL Management
    async getUrls() {
        return this.request('/api/urls');
    }

    async uploadUrls(content) {
        return this.request('/api/urls', {
            method: 'POST',
            body: JSON.stringify({ content })
        });
    }

    async resetUrls() {
        return this.request('/api/urls', {
            method: 'DELETE'
        });
    }

    // Event Management
    async getEvents() {
        return this.request('/api/events');
    }

    async uploadEvents(content) {
        return this.request('/api/events', {
            method: 'POST',
            body: JSON.stringify({ content })
        });
    }

    async resetEvents() {
        return this.request('/api/events', {
            method: 'DELETE'
        });
    }

    // Funnel Management
    async getFunnels() {
        return this.request('/api/funnels');
    }

    async getFunnel(id) {
        return this.request(`/api/funnels/${id}`);
    }

    async createFunnel(payload) {
        return this.request('/api/funnels', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }

    async updateFunnel(id, payload) {
        return this.request(`/api/funnels/${id}`, {
            method: 'PUT',
            body: JSON.stringify(payload)
        });
    }

    async deleteFunnel(id) {
        return this.request(`/api/funnels/${id}`, {
            method: 'DELETE'
        });
    }

    // Backfill (one-off)
    async runBackfill(payload) {
        return this.request('/api/backfill/run', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }

    async backfillStatus() {
        return this.request('/api/backfill/status');
    }

    async backfillCleanup() {
        return this.request('/api/backfill/cleanup', { method: 'POST' });
    }

    async backfillLast() {
        return this.request('/api/backfill/last');
    }

    async backfillCancel(containerName) {
        return this.request('/api/backfill/cancel', {
            method: 'POST',
            body: JSON.stringify({ container_name: containerName })
        });
    }
}

// Create global API instance
window.api = new API();

// API Key Management UI
const APIKeyManager = {
    init() {
        this.checkApiKey();
    },

    checkApiKey() {
        if (!api.hasApiKey()) {
            this.showApiKeyPrompt();
        } else {
            this.verifyApiKey();
        }
    },

    showApiKeyPrompt() {
        const key = prompt('Please enter your API key:');
        if (key) {
            api.saveApiKey(key);
            this.verifyApiKey();
        } else {
            UI.showAlert('API key is required to use this application', 'error', 0);
        }
    },

    async verifyApiKey() {
        try {
            UI.showLoading('Verifying API key...');
            await api.getStatus();
            UI.hideLoading();
            UI.updateConnectionStatus(true, 'Connected');
        } catch (error) {
            UI.hideLoading();
            UI.updateConnectionStatus(false, 'Authentication Failed');
            
            if (error.message.includes('Authentication failed')) {
                UI.showAlert('Invalid API key. Please enter a valid key.', 'error', 0);
                api.clearApiKey();
                this.showApiKeyPrompt();
            } else {
                UI.showAlert(error.message, 'error');
            }
        }
    },

    changeApiKey() {
        api.clearApiKey();
        this.showApiKeyPrompt();
    }
};

// Export for use in app
window.APIKeyManager = APIKeyManager;
