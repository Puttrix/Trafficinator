// UI Helper Functions
const UI = {
    // Show loading overlay
    showLoading(message = 'Loading...') {
        const overlay = document.getElementById('loading-overlay');
        const text = document.getElementById('loading-text');
        text.textContent = message;
        overlay.classList.remove('hidden');
    },

    // Hide loading overlay
    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        overlay.classList.add('hidden');
    },

    // Show alert message
    showAlert(message, type = 'info', duration = 5000) {
        const container = document.getElementById('alert-container');
        const alertId = 'alert-' + Date.now();
        
        const colors = {
            success: 'bg-green-50 border-green-200 text-green-800',
            error: 'bg-red-50 border-red-200 text-red-800',
            warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
            info: 'bg-blue-50 border-blue-200 text-blue-800'
        };

        const icons = {
            success: `<svg class="w-5 h-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
            </svg>`,
            error: `<svg class="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
            </svg>`,
            warning: `<svg class="w-5 h-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
            </svg>`,
            info: `<svg class="w-5 h-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
            </svg>`
        };

        const alertHTML = `
            <div id="${alertId}" class="border rounded-lg p-4 mb-4 flex items-start gap-3 ${colors[type] || colors.info}">
                <div class="flex-shrink-0 mt-0.5">
                    ${icons[type] || icons.info}
                </div>
                <div class="flex-1">
                    <p class="text-sm font-medium">${message}</p>
                </div>
                <button onclick="UI.dismissAlert('${alertId}')" class="flex-shrink-0 ml-3 inline-flex text-gray-400 hover:text-gray-500">
                    <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                    </svg>
                </button>
            </div>
        `;

        container.insertAdjacentHTML('beforeend', alertHTML);

        if (duration > 0) {
            setTimeout(() => this.dismissAlert(alertId), duration);
        }

        return alertId;
    },

    // Dismiss alert by ID
    dismissAlert(alertId) {
        const alert = document.getElementById(alertId);
        if (alert) {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.3s';
            setTimeout(() => alert.remove(), 300);
        }
    },

    // Clear all alerts
    clearAlerts() {
        const container = document.getElementById('alert-container');
        container.innerHTML = '';
    },

    // Update connection status indicator
    updateConnectionStatus(connected, message = '') {
        const statusDiv = document.getElementById('connection-status');
        if (!statusDiv) return;

        const dot = statusDiv.querySelector('div');
        const text = statusDiv.querySelector('span');

        if (connected) {
            dot.className = 'w-2 h-2 rounded-full bg-green-500 animate-pulse';
            text.textContent = message || 'Connected';
            text.className = 'text-sm text-green-600';
        } else {
            dot.className = 'w-2 h-2 rounded-full bg-red-500';
            text.textContent = message || 'Disconnected';
            text.className = 'text-sm text-red-600';
        }
    },

    // Tab Management
    switchTab(tabName) {
        // Update tab buttons
        const tabButtons = document.querySelectorAll('.tab-button');
        tabButtons.forEach(button => {
            if (button.dataset.tab === tabName) {
                button.classList.add('tab-active');
            } else {
                button.classList.remove('tab-active');
            }
        });

        // Update tab content
        const tabContents = document.querySelectorAll('.tab-content');
        tabContents.forEach(content => {
            if (content.id === 'tab-' + tabName) {
                content.classList.remove('hidden');
            } else {
                content.classList.add('hidden');
            }
        });

        // Store current tab in localStorage
        localStorage.setItem('currentTab', tabName);
    },

    // Initialize tab navigation
    initTabs() {
        const tabButtons = document.querySelectorAll('.tab-button');
        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                this.switchTab(button.dataset.tab);
            });
        });

        // Restore last active tab or default to status
        const lastTab = localStorage.getItem('currentTab') || 'status';
        this.switchTab(lastTab);
    },

    // Format timestamp
    formatTimestamp(timestamp) {
        if (!timestamp) return 'N/A';
        const date = new Date(timestamp);
        return date.toLocaleString();
    },

    // Format duration in seconds to human readable
    formatDuration(seconds) {
        if (!seconds || seconds < 0) return 'N/A';
        
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);

        const parts = [];
        if (days > 0) parts.push(`${days}d`);
        if (hours > 0) parts.push(`${hours}h`);
        if (minutes > 0) parts.push(`${minutes}m`);
        if (secs > 0 || parts.length === 0) parts.push(`${secs}s`);

        return parts.join(' ');
    },

    // Format bytes to human readable
    formatBytes(bytes) {
        if (!bytes || bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    // Confirm dialog
    confirm(message, onConfirm, onCancel) {
        if (window.confirm(message)) {
            if (onConfirm) onConfirm();
        } else {
            if (onCancel) onCancel();
        }
    },

    // Escape HTML to prevent XSS
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// Export for use in other modules
window.UI = UI;
