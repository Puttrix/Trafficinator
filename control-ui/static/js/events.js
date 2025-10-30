/**
 * Event Management Module
 * Handles event configuration loading, editing, validation, and upload
 */

class EventManager {
    constructor() {
        this.config = null;
        this.currentSource = null;
        this.validationResults = null;
    }

    init() {
        this.setupEventListeners();
        this.updateLineCount();
    }

    setupEventListeners() {
        // Button listeners
        document.getElementById('btn-load-events').addEventListener('click', () => this.loadEvents());
        document.getElementById('btn-validate-events').addEventListener('click', () => this.validateEvents());
        document.getElementById('btn-save-events').addEventListener('click', () => this.saveEvents());
        document.getElementById('btn-download-events').addEventListener('click', () => this.downloadEvents());
        document.getElementById('btn-reset-events').addEventListener('click', () => this.resetEvents());
        document.getElementById('btn-upload-events-file').addEventListener('click', () => {
            document.getElementById('events-file-input').click();
        });
        
        // File upload
        document.getElementById('events-file-input').addEventListener('change', (e) => this.handleFileUpload(e));
        
        // Editor changes
        const editor = document.getElementById('events-editor');
        editor.addEventListener('input', () => {
            this.updateLineCount();
            this.hideValidationResults();
        });
    }

    updateLineCount() {
        const editor = document.getElementById('events-editor');
        const lineCount = editor.value.split('\n').length;
        document.getElementById('events-line-count').textContent = lineCount;
    }

    async loadEvents() {
        UI.showLoading('Loading events...');
        
        try {
            const data = await api.getEvents();
            
            // Update editor with formatted JSON
            document.getElementById('events-editor').value = JSON.stringify(data.config, null, 2);
            this.updateLineCount();
            
            // Update status
            const clickCount = data.config.click_events?.length || 0;
            const randomCount = data.config.random_events?.length || 0;
            const clickProb = ((data.config.click_events_probability || 0) * 100).toFixed(0);
            const randomProb = ((data.config.random_events_probability || 0) * 100).toFixed(0);
            
            document.getElementById('events-click-count').textContent = clickCount;
            document.getElementById('events-random-count').textContent = randomCount;
            document.getElementById('events-source').textContent = `source: ${data.source}`;
            document.getElementById('events-click-prob').textContent = `${clickProb}%`;
            document.getElementById('events-random-prob').textContent = `${randomProb}%`;
            
            // Store data
            this.config = data.config;
            this.currentSource = data.source;
            this.validationResults = data.validation;
            
            // Show statistics if available
            if (data.validation && data.validation.stats) {
                this.displayStatistics(data.validation.stats);
            }
            
            UI.hideLoading();
            UI.showAlert(`Loaded ${clickCount} click events and ${randomCount} random events from ${data.source}`, 'success');
        } catch (error) {
            UI.hideLoading();
            UI.showAlert(`Failed to load events: ${error.message}`, 'error');
        }
    }

    async validateEvents() {
        const content = document.getElementById('events-editor').value;
        
        if (!content.trim()) {
            UI.showAlert('Please enter event configuration to validate', 'warning');
            return;
        }
        
        UI.showLoading('Validating events...');
        
        try {
            const response = await fetch('/api/events/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': api.apiKey
                },
                body: JSON.stringify({ content })
            });
            
            if (!response.ok) {
                throw new Error('Validation request failed');
            }
            
            const data = await response.json();
            this.validationResults = data;
            
            UI.hideLoading();
            this.displayValidationResults(data);
            
            if (data.valid) {
                UI.showAlert(`Validation passed: ${data.stats.click_events_count} click events, ${data.stats.random_events_count} random events`, 'success');
                if (data.stats) {
                    this.displayStatistics(data.stats);
                }
            } else {
                UI.showAlert(`Validation failed: ${data.errors.length} errors found`, 'error');
            }
        } catch (error) {
            UI.hideLoading();
            UI.showAlert(`Validation error: ${error.message}`, 'error');
        }
    }

    async saveEvents() {
        const content = document.getElementById('events-editor').value;
        
        if (!content.trim()) {
            UI.showAlert('Please enter event configuration to save', 'warning');
            return;
        }
        
        const confirmed = confirm(
            'Save these events? The container will need to be restarted for changes to take effect.'
        );
        
        if (!confirmed) return;
        
        UI.showLoading('Saving events...');
        
        try {
            const data = await api.uploadEvents(content);
            
            UI.hideLoading();
            
            if (data.success) {
                UI.showAlert(data.message, 'success');
                if (data.validation) {
                    this.displayValidationResults(data.validation);
                    if (data.validation.stats) {
                        this.displayStatistics(data.validation.stats);
                    }
                }
                
                // Reload to show new status
                await this.loadEvents();
            } else {
                UI.showAlert(data.message || 'Failed to save events', 'error');
                if (data.validation) {
                    this.displayValidationResults(data.validation);
                }
            }
        } catch (error) {
            UI.hideLoading();
            UI.showAlert(`Failed to save events: ${error.message}`, 'error');
        }
    }

    downloadEvents() {
        const content = document.getElementById('events-editor').value;
        
        if (!content.trim()) {
            UI.showAlert('No events to download', 'warning');
            return;
        }
        
        // Format JSON nicely
        try {
            const config = JSON.parse(content);
            const formatted = JSON.stringify(config, null, 2);
            
            // Create blob and download
            const blob = new Blob([formatted], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `events-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            UI.showAlert('Events downloaded', 'success');
        } catch (error) {
            UI.showAlert('Invalid JSON - cannot download', 'error');
        }
    }

    async resetEvents() {
        const confirmed = confirm(
            'Reset events to defaults? This will delete your custom events. The container will need to be restarted for changes to take effect.'
        );
        
        if (!confirmed) return;
        
        UI.showLoading('Resetting events...');
        
        try {
            const data = await api.resetEvents();
            
            UI.hideLoading();
            
            if (data.success) {
                UI.showAlert(data.message, 'success');
                
                // Reload to show default events
                await this.loadEvents();
            } else {
                UI.showAlert(data.message || 'Failed to reset events', 'error');
            }
        } catch (error) {
            UI.hideLoading();
            UI.showAlert(`Failed to reset events: ${error.message}`, 'error');
        }
    }

    handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        if (!file.name.endsWith('.json')) {
            UI.showAlert('Please upload a .json file', 'warning');
            return;
        }
        
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                // Validate JSON
                const config = JSON.parse(e.target.result);
                
                // Format and set
                document.getElementById('events-editor').value = JSON.stringify(config, null, 2);
                this.updateLineCount();
                UI.showAlert(`Loaded file: ${file.name}`, 'success');
            } catch (error) {
                UI.showAlert(`Invalid JSON file: ${error.message}`, 'error');
            }
        };
        reader.onerror = () => {
            UI.showAlert('Failed to read file', 'error');
        };
        reader.readAsText(file);
        
        // Reset input
        event.target.value = '';
    }

    displayValidationResults(validation) {
        const container = document.getElementById('events-validation-results');
        const content = document.getElementById('events-validation-content');
        
        let html = '';
        
        // Summary
        html += `
            <div class="flex items-center gap-2 text-sm">
                ${validation.valid 
                    ? '<svg class="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path></svg>'
                    : '<svg class="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path></svg>'
                }
                <span class="font-medium">${validation.valid ? 'Valid' : 'Invalid'}</span>
                ${validation.stats ? `
                    <span class="text-gray-500">•</span>
                    <span>${validation.stats.click_events_count} click events</span>
                    <span class="text-gray-500">•</span>
                    <span>${validation.stats.random_events_count} random events</span>
                ` : ''}
            </div>
        `;
        
        // Errors
        if (validation.errors && validation.errors.length > 0) {
            html += '<div class="mt-3 space-y-1">';
            html += '<p class="text-sm font-medium text-red-600">Errors:</p>';
            validation.errors.forEach(error => {
                html += `<p class="text-sm text-red-600 pl-4">• ${UI.escapeHtml(error)}</p>`;
            });
            html += '</div>';
        }
        
        // Warnings
        if (validation.warnings && validation.warnings.length > 0) {
            html += '<div class="mt-3 space-y-1">';
            html += '<p class="text-sm font-medium text-yellow-600">Warnings:</p>';
            validation.warnings.forEach(warning => {
                html += `<p class="text-sm text-yellow-600 pl-4">• ${UI.escapeHtml(warning)}</p>`;
            });
            html += '</div>';
        }
        
        content.innerHTML = html;
        container.classList.remove('hidden');
    }

    displayStatistics(stats) {
        const container = document.getElementById('events-statistics-preview');
        const content = document.getElementById('events-statistics-content');
        
        let html = '';
        
        // Summary stats
        html += `
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="bg-gray-50 rounded-lg p-3">
                    <p class="text-xs text-gray-500">Click Events</p>
                    <p class="text-2xl font-bold text-gray-900">${stats.click_events_count}</p>
                </div>
                <div class="bg-gray-50 rounded-lg p-3">
                    <p class="text-xs text-gray-500">Random Events</p>
                    <p class="text-2xl font-bold text-gray-900">${stats.random_events_count}</p>
                </div>
                <div class="bg-gray-50 rounded-lg p-3">
                    <p class="text-xs text-gray-500">Click Probability</p>
                    <p class="text-2xl font-bold text-gray-900">${(stats.click_events_probability * 100).toFixed(0)}%</p>
                </div>
                <div class="bg-gray-50 rounded-lg p-3">
                    <p class="text-xs text-gray-500">Random Probability</p>
                    <p class="text-2xl font-bold text-gray-900">${(stats.random_events_probability * 100).toFixed(0)}%</p>
                </div>
            </div>
        `;
        
        // Click event categories
        if (stats.click_event_categories && Object.keys(stats.click_event_categories).length > 0) {
            html += '<div class="mt-4">';
            html += '<p class="text-sm font-medium text-gray-700 mb-2">Click Event Categories:</p>';
            
            const categories = Object.entries(stats.click_event_categories)
                .sort((a, b) => b[1] - a[1]);
            
            categories.forEach(([category, count]) => {
                const percentage = ((count / stats.click_events_count) * 100).toFixed(1);
                html += `
                    <div class="flex items-center gap-2 mb-2">
                        <span class="text-sm text-gray-600 w-32 truncate">${UI.escapeHtml(category)}</span>
                        <div class="flex-1 bg-gray-200 rounded-full h-2">
                            <div class="bg-blue-500 h-2 rounded-full" style="width: ${percentage}%"></div>
                        </div>
                        <span class="text-sm text-gray-500 w-16 text-right">${count} (${percentage}%)</span>
                    </div>
                `;
            });
            
            html += '</div>';
        }
        
        // Random event categories
        if (stats.random_event_categories && Object.keys(stats.random_event_categories).length > 0) {
            html += '<div class="mt-4">';
            html += '<p class="text-sm font-medium text-gray-700 mb-2">Random Event Categories:</p>';
            
            const categories = Object.entries(stats.random_event_categories)
                .sort((a, b) => b[1] - a[1]);
            
            categories.forEach(([category, count]) => {
                const percentage = ((count / stats.random_events_count) * 100).toFixed(1);
                html += `
                    <div class="flex items-center gap-2 mb-2">
                        <span class="text-sm text-gray-600 w-32 truncate">${UI.escapeHtml(category)}</span>
                        <div class="flex-1 bg-gray-200 rounded-full h-2">
                            <div class="bg-green-500 h-2 rounded-full" style="width: ${percentage}%"></div>
                        </div>
                        <span class="text-sm text-gray-500 w-16 text-right">${count} (${percentage}%)</span>
                    </div>
                `;
            });
            
            html += '</div>';
        }
        
        content.innerHTML = html;
        container.classList.remove('hidden');
    }

    hideValidationResults() {
        document.getElementById('events-validation-results').classList.add('hidden');
        document.getElementById('events-statistics-preview').classList.add('hidden');
    }

    // Lifecycle methods
    onTabActivated() {
        // Load events when tab is first activated
        if (!this.config) {
            this.loadEvents();
        }
    }

    onTabDeactivated() {
        // Nothing to clean up
    }
}
