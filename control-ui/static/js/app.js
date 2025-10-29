// Main Application Controller
class App {
    constructor() {
        this.refreshInterval = null;
        this.currentTab = 'status';
    }

    // Initialize application
    async init() {
        console.log('Initializing Matomo Load Generator Control UI...');

        // Initialize UI components
        UI.initTabs();

        // Initialize API key management
        APIKeyManager.init();

        // Initialize configuration form
        this.configForm = new ConfigForm();
        this.configForm.init();

        // Initialize status dashboard
        this.statusDashboard = new StatusDashboard();
        this.statusDashboard.init();

        // Initialize load presets
        this.loadPresets = new LoadPresets();
        this.loadPresets.init();

        // Initialize log viewer
        this.logViewer = new LogViewer();
        this.logViewer.init();

        // Initialize URL manager
        this.urlManager = new URLManager();
        this.urlManager.init();

        // Set up event listeners
        this.setupEventListeners();

        // Start auto-refresh for status tab if active
        this.startAutoRefresh();

        console.log('Application initialized successfully');
    }

    // Setup global event listeners
    setupEventListeners() {
        // Tab change listener
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', () => {
                this.currentTab = button.dataset.tab;
                this.handleTabChange(button.dataset.tab);
            });
        });

        // Handle visibility change (pause refresh when tab is hidden)
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopAutoRefresh();
            } else {
                this.startAutoRefresh();
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K to change API key
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                APIKeyManager.changeApiKey();
            }
        });
    }

    // Handle tab changes
    handleTabChange(tabName) {
        console.log('Tab changed to:', tabName);

        // Clear any existing refresh intervals
        this.stopAutoRefresh();

        // Notify modules of tab deactivation
        if (this.currentTab === 'logs' && this.logViewer) {
            this.logViewer.onTabDeactivated();
        }
        if (this.currentTab === 'urls' && this.urlManager) {
            this.urlManager.onTabDeactivated();
        }

        // Start refresh for status tab
        if (tabName === 'status') {
            this.startAutoRefresh();
        }

        // Notify modules of tab activation
        if (tabName === 'logs' && this.logViewer) {
            this.logViewer.onTabActivated();
        }
        if (tabName === 'urls' && this.urlManager) {
            this.urlManager.onTabActivated();
        }

        // Load tab-specific data
        switch (tabName) {
            case 'status':
                this.loadStatusData();
                break;
            case 'config':
                // Config form will load in P-021
                break;
            case 'presets':
                // Presets will load in P-022
                break;
            case 'logs':
                // Logs tab auto-loads via onTabActivated
                break;
            case 'urls':
                // URLs tab auto-loads via onTabActivated
                break;
        }
    }

    // Load status data
    async loadStatusData() {
        if (this.statusDashboard) {
            await this.statusDashboard.loadStatus();
        }
    }

    // Start auto-refresh for active tab
    startAutoRefresh() {
        if (this.currentTab === 'status' && this.statusDashboard) {
            this.statusDashboard.startAutoRefresh();
        }
    }

    // Stop auto-refresh
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
        
        // Also stop status dashboard refresh
        if (this.statusDashboard) {
            this.statusDashboard.stopAutoRefresh();
        }
    }

    // Handle errors globally
    handleError(error, context = '') {
        console.error(`Error in ${context}:`, error);
        
        let message = error.message || 'An unexpected error occurred';
        
        // Add context if provided
        if (context) {
            message = `${context}: ${message}`;
        }

        UI.showAlert(message, 'error');
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
    app.init().catch(error => {
        console.error('Failed to initialize application:', error);
        UI.showAlert('Failed to initialize application. Please refresh the page.', 'error', 0);
    });
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    UI.showAlert(`Unhandled error: ${event.reason?.message || 'Unknown error'}`, 'error');
});
