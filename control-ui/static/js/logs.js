// Log Viewer Management
class LogViewer {
    constructor() {
        this.logs = [];
        this.filteredLogs = [];
        this.autoScroll = true;
        this.autoRefresh = false;
        this.refreshInterval = null;
        this.currentLines = 100;
        this.searchTerm = '';
    }

    // Initialize log viewer
    init() {
        this.setupEventListeners();
        this.loadLogs();
    }

    // Setup event listeners
    setupEventListeners() {
        // Line count selector
        const lineCountSelect = document.getElementById('log-lines-select');
        if (lineCountSelect) {
            lineCountSelect.addEventListener('change', (e) => {
                this.currentLines = parseInt(e.target.value);
                this.loadLogs();
            });
        }

        // Refresh button
        const refreshBtn = document.getElementById('refresh-logs-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadLogs());
        }

        // Clear button
        const clearBtn = document.getElementById('clear-logs-btn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearLogs());
        }

        // Copy button
        const copyBtn = document.getElementById('copy-logs-btn');
        if (copyBtn) {
            copyBtn.addEventListener('click', () => this.copyLogs());
        }

        // Auto-scroll toggle
        const autoScrollToggle = document.getElementById('auto-scroll-toggle');
        if (autoScrollToggle) {
            autoScrollToggle.addEventListener('change', (e) => {
                this.autoScroll = e.target.checked;
                if (this.autoScroll) {
                    this.scrollToBottom();
                }
            });
        }

        // Auto-refresh toggle
        const autoRefreshToggle = document.getElementById('auto-refresh-toggle');
        if (autoRefreshToggle) {
            autoRefreshToggle.addEventListener('change', (e) => {
                this.autoRefresh = e.target.checked;
                if (this.autoRefresh) {
                    this.startAutoRefresh();
                } else {
                    this.stopAutoRefresh();
                }
            });
        }

        // Search input
        const searchInput = document.getElementById('log-search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.searchTerm = e.target.value.toLowerCase();
                this.filterLogs();
            });
        }

        // Log container scroll detection (disable auto-scroll if user scrolls up)
        const logContainer = document.getElementById('log-content');
        if (logContainer) {
            logContainer.addEventListener('scroll', () => {
                const isAtBottom = logContainer.scrollHeight - logContainer.scrollTop <= logContainer.clientHeight + 50;
                const autoScrollToggle = document.getElementById('auto-scroll-toggle');
                if (autoScrollToggle && !isAtBottom) {
                    autoScrollToggle.checked = false;
                    this.autoScroll = false;
                }
            });
        }
    }

    // Load logs from API
    async loadLogs() {
        const refreshBtn = document.getElementById('refresh-logs-btn');
        const originalText = refreshBtn ? refreshBtn.innerHTML : '';
        
        try {
            // Show loading state
            if (refreshBtn) {
                refreshBtn.disabled = true;
                refreshBtn.innerHTML = '<svg class="animate-spin h-4 w-4 inline-block" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Loading...';
            }

            const result = await api.getLogs(this.currentLines);
            
            if (result.logs && Array.isArray(result.logs)) {
                this.logs = result.logs;
                this.filterLogs();
                
                // Update stats
                this.updateStats(result.logs.length, result.container_status);
            } else {
                this.logs = [];
                this.filteredLogs = [];
                this.renderLogs();
                UI.showAlert('No logs available', 'info');
            }
            
        } catch (error) {
            console.error('Failed to load logs:', error);
            this.logs = [];
            this.filteredLogs = [];
            this.renderLogs();
            UI.showAlert(`Failed to load logs: ${error.message}`, 'error');
        } finally {
            // Restore button state
            if (refreshBtn) {
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = originalText;
            }
        }
    }

    // Filter logs based on search term
    filterLogs() {
        if (!this.searchTerm) {
            this.filteredLogs = [...this.logs];
        } else {
            this.filteredLogs = this.logs.filter(log => 
                log.toLowerCase().includes(this.searchTerm)
            );
        }
        
        this.renderLogs();
        this.updateFilterStats();
    }

    // Render logs to the display
    renderLogs() {
        const logContent = document.getElementById('log-content');
        if (!logContent) return;

        if (this.filteredLogs.length === 0) {
            logContent.innerHTML = '<div class="text-center text-gray-500 py-8">No logs to display</div>';
            return;
        }

        // Build log lines
        let html = '<div class="font-mono text-sm">';
        this.filteredLogs.forEach((line, index) => {
            const lineClass = this.getLogLineClass(line);
            const lineNumber = index + 1;
            
            html += `
                <div class="log-line ${lineClass} hover:bg-gray-50 px-3 py-1 border-b border-gray-100">
                    <span class="text-gray-400 select-none mr-3 inline-block w-12 text-right">${lineNumber}</span>
                    <span class="whitespace-pre-wrap break-all">${this.escapeHtml(line)}</span>
                </div>
            `;
        });
        html += '</div>';

        logContent.innerHTML = html;

        // Auto-scroll if enabled
        if (this.autoScroll) {
            this.scrollToBottom();
        }
    }

    // Get CSS class for log line based on content
    getLogLineClass(line) {
        const lineLower = line.toLowerCase();
        
        if (lineLower.includes('error') || lineLower.includes('exception') || lineLower.includes('failed')) {
            return 'text-red-700 bg-red-50';
        }
        if (lineLower.includes('warning') || lineLower.includes('warn')) {
            return 'text-yellow-700 bg-yellow-50';
        }
        if (lineLower.includes('info')) {
            return 'text-blue-700';
        }
        if (lineLower.includes('debug')) {
            return 'text-gray-600';
        }
        if (lineLower.includes('success') || lineLower.includes('✅')) {
            return 'text-green-700';
        }
        
        return 'text-gray-800';
    }

    // Escape HTML to prevent XSS
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Update statistics
    updateStats(totalLines, containerStatus) {
        const totalLinesEl = document.getElementById('log-total-lines');
        const containerStatusEl = document.getElementById('log-container-status');
        
        if (totalLinesEl) {
            totalLinesEl.textContent = totalLines.toLocaleString();
        }
        
        if (containerStatusEl) {
            const statusColors = {
                running: 'text-green-600',
                stopped: 'text-gray-600',
                exited: 'text-gray-600',
                error: 'text-red-600'
            };
            
            containerStatusEl.textContent = containerStatus || 'unknown';
            containerStatusEl.className = `font-medium ${statusColors[containerStatus] || 'text-gray-600'}`;
        }
    }

    // Update filter statistics
    updateFilterStats() {
        const filteredCountEl = document.getElementById('log-filtered-count');
        if (filteredCountEl) {
            if (this.searchTerm) {
                filteredCountEl.textContent = `(${this.filteredLogs.length} filtered)`;
                filteredCountEl.classList.remove('hidden');
            } else {
                filteredCountEl.classList.add('hidden');
            }
        }
    }

    // Clear logs display
    clearLogs() {
        UI.confirm(
            'Clear the log display? This will only clear the view, not the actual container logs.',
            () => {
                this.logs = [];
                this.filteredLogs = [];
                this.searchTerm = '';
                
                const searchInput = document.getElementById('log-search-input');
                if (searchInput) {
                    searchInput.value = '';
                }
                
                this.renderLogs();
                this.updateStats(0, 'cleared');
                this.updateFilterStats();
            }
        );
    }

    // Copy logs to clipboard
    async copyLogs() {
        if (this.filteredLogs.length === 0) {
            UI.showAlert('No logs to copy', 'warning');
            return;
        }

        try {
            const logsText = this.filteredLogs.join('\n');
            await navigator.clipboard.writeText(logsText);
            UI.showAlert(`✅ Copied ${this.filteredLogs.length} log lines to clipboard`, 'success');
        } catch (error) {
            console.error('Failed to copy logs:', error);
            UI.showAlert('Failed to copy logs to clipboard', 'error');
        }
    }

    // Scroll to bottom of log container
    scrollToBottom() {
        const logContent = document.getElementById('log-content');
        if (logContent) {
            logContent.scrollTop = logContent.scrollHeight;
        }
    }

    // Start auto-refresh
    startAutoRefresh() {
        this.stopAutoRefresh();
        
        // Refresh every 2 seconds (P-024 requirement)
        this.refreshInterval = setInterval(() => {
            this.loadLogs();
        }, 2000);
        
        console.log('Log auto-refresh started (every 2 seconds)');
    }

    // Stop auto-refresh
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
            console.log('Log auto-refresh stopped');
        }
    }

    // Handle tab activation (start/stop auto-refresh based on container status)
    async onTabActivated() {
        // Check if container is running
        try {
            const status = await api.getStatus();
            const autoRefreshToggle = document.getElementById('auto-refresh-toggle');
            
            if (status.status === 'running' && autoRefreshToggle) {
                // Enable auto-refresh if container is running
                autoRefreshToggle.disabled = false;
                if (autoRefreshToggle.checked) {
                    this.startAutoRefresh();
                }
            } else if (autoRefreshToggle) {
                // Disable auto-refresh if container is not running
                autoRefreshToggle.disabled = true;
                autoRefreshToggle.checked = false;
                this.stopAutoRefresh();
            }
        } catch (error) {
            console.error('Failed to check container status:', error);
        }
        
        // Load logs initially
        await this.loadLogs();
    }

    // Handle tab deactivation
    onTabDeactivated() {
        this.stopAutoRefresh();
    }
}

// Export for use in app
window.LogViewer = LogViewer;
