/**
 * URL Management Module
 * Handles URL loading, editing, validation, and upload
 */

class URLManager {
    constructor() {
        this.urls = null;
        this.currentSource = null;
        this.validationResults = null;
        this.structureData = null;
    }

    init() {
        this.setupEventListeners();
        this.updateLineCount();
    }

    setupEventListeners() {
        // Button listeners
        document.getElementById('btn-load-urls').addEventListener('click', () => this.loadUrls());
        document.getElementById('btn-validate-urls').addEventListener('click', () => this.validateUrls());
        document.getElementById('btn-save-urls').addEventListener('click', () => this.saveUrls());
        document.getElementById('btn-download-urls').addEventListener('click', () => this.downloadUrls());
        document.getElementById('btn-reset-urls').addEventListener('click', () => this.resetUrls());
        document.getElementById('btn-upload-file').addEventListener('click', () => {
            document.getElementById('urls-file-input').click();
        });
        
        // File upload
        document.getElementById('urls-file-input').addEventListener('change', (e) => this.handleFileUpload(e));
        
        // Editor changes
        const editor = document.getElementById('urls-editor');
        editor.addEventListener('input', () => {
            this.updateLineCount();
            this.hideValidationResults();
        });
    }

    updateLineCount() {
        const editor = document.getElementById('urls-editor');
        const lineCount = editor.value.split('\n').length;
        document.getElementById('urls-line-count').textContent = lineCount;
    }

    async loadUrls() {
        UI.showLoading('Loading URLs...');
        
        try {
            const data = await API.getUrls();
            
            // Update editor
            document.getElementById('urls-editor').value = data.content;
            this.updateLineCount();
            
            // Update status
            document.getElementById('urls-count').textContent = data.validation?.url_count || 0;
            document.getElementById('urls-source').textContent = `source: ${data.source}`;
            
            // Store data
            this.urls = data;
            this.validationResults = data.validation;
            this.structureData = data.structure;
            
            // Show structure if available
            if (data.structure) {
                this.displayStructure(data.structure);
            }
            
            UI.hideLoading();
            UI.showAlert(`Loaded ${data.validation?.url_count || 0} URLs from ${data.source}`, 'success');
        } catch (error) {
            UI.hideLoading();
            UI.showAlert(`Failed to load URLs: ${error.message}`, 'error');
        }
    }

    async validateUrls() {
        const content = document.getElementById('urls-editor').value;
        
        if (!content.trim()) {
            UI.showAlert('Please enter some URLs to validate', 'warning');
            return;
        }
        
        UI.showLoading('Validating URLs...');
        
        try {
            // Use API validation endpoint (note: we'll need to create this or validate locally)
            const response = await fetch('/api/urls/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': API.apiKey
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
                UI.showAlert(`Validation passed: ${data.url_count} valid URLs`, 'success');
                if (data.structure) {
                    this.displayStructure(data.structure);
                }
            } else {
                UI.showAlert(`Validation failed: ${data.errors.length} errors found`, 'error');
            }
        } catch (error) {
            UI.hideLoading();
            UI.showAlert(`Validation error: ${error.message}`, 'error');
        }
    }

    async saveUrls() {
        const content = document.getElementById('urls-editor').value;
        
        if (!content.trim()) {
            UI.showAlert('Please enter some URLs to save', 'warning');
            return;
        }
        
        const confirmed = confirm(
            'Save these URLs? The container will need to be restarted for changes to take effect.'
        );
        
        if (!confirmed) return;
        
        UI.showLoading('Saving URLs...');
        
        try {
            const data = await API.uploadUrls(content);
            
            UI.hideLoading();
            
            if (data.success) {
                UI.showAlert(data.message, 'success');
                if (data.validation) {
                    this.displayValidationResults(data.validation);
                }
                if (data.structure) {
                    this.displayStructure(data.structure);
                }
                
                // Reload to show new status
                await this.loadUrls();
            } else {
                UI.showAlert(data.message || 'Failed to save URLs', 'error');
                if (data.validation) {
                    this.displayValidationResults(data.validation);
                }
            }
        } catch (error) {
            UI.hideLoading();
            UI.showAlert(`Failed to save URLs: ${error.message}`, 'error');
        }
    }

    downloadUrls() {
        const content = document.getElementById('urls-editor').value;
        
        if (!content.trim()) {
            UI.showAlert('No URLs to download', 'warning');
            return;
        }
        
        // Create blob and download
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `urls-${new Date().toISOString().split('T')[0]}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        UI.showAlert('URLs downloaded', 'success');
    }

    async resetUrls() {
        const confirmed = confirm(
            'Reset URLs to defaults? This will delete your custom URLs. The container will need to be restarted for changes to take effect.'
        );
        
        if (!confirmed) return;
        
        UI.showLoading('Resetting URLs...');
        
        try {
            const data = await API.resetUrls();
            
            UI.hideLoading();
            
            if (data.success) {
                UI.showAlert(data.message, 'success');
                
                // Reload to show default URLs
                await this.loadUrls();
            } else {
                UI.showAlert(data.message || 'Failed to reset URLs', 'error');
            }
        } catch (error) {
            UI.hideLoading();
            UI.showAlert(`Failed to reset URLs: ${error.message}`, 'error');
        }
    }

    handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        if (!file.name.endsWith('.txt')) {
            UI.showAlert('Please upload a .txt file', 'warning');
            return;
        }
        
        const reader = new FileReader();
        reader.onload = (e) => {
            document.getElementById('urls-editor').value = e.target.result;
            this.updateLineCount();
            UI.showAlert(`Loaded file: ${file.name}`, 'success');
        };
        reader.onerror = () => {
            UI.showAlert('Failed to read file', 'error');
        };
        reader.readAsText(file);
        
        // Reset input
        event.target.value = '';
    }

    displayValidationResults(validation) {
        const container = document.getElementById('urls-validation-results');
        const content = document.getElementById('urls-validation-content');
        
        let html = '';
        
        // Summary
        html += `
            <div class="flex items-center gap-2 text-sm">
                ${validation.valid 
                    ? '<svg class="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path></svg>'
                    : '<svg class="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path></svg>'
                }
                <span class="font-medium">${validation.valid ? 'Valid' : 'Invalid'}</span>
                <span class="text-gray-500">•</span>
                <span>${validation.url_count} URLs found</span>
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

    displayStructure(structure) {
        const container = document.getElementById('urls-structure-preview');
        const content = document.getElementById('urls-structure-content');
        
        let html = '';
        
        // Summary stats
        html += `
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div class="bg-gray-50 rounded-lg p-3">
                    <p class="text-xs text-gray-500">Total URLs</p>
                    <p class="text-2xl font-bold text-gray-900">${structure.total_urls}</p>
                </div>
                <div class="bg-gray-50 rounded-lg p-3">
                    <p class="text-xs text-gray-500">Categories</p>
                    <p class="text-2xl font-bold text-gray-900">${structure.total_categories}</p>
                </div>
                <div class="bg-gray-50 rounded-lg p-3">
                    <p class="text-xs text-gray-500">Subcategories</p>
                    <p class="text-2xl font-bold text-gray-900">${structure.total_subcategories}</p>
                </div>
                <div class="bg-gray-50 rounded-lg p-3">
                    <p class="text-xs text-gray-500">Domains</p>
                    <p class="text-2xl font-bold text-gray-900">${structure.unique_domains}</p>
                </div>
            </div>
        `;
        
        // Category breakdown
        if (structure.categories) {
            html += '<div class="space-y-2">';
            html += '<p class="text-sm font-medium text-gray-700">Category Distribution:</p>';
            
            const categories = Object.entries(structure.categories)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 10); // Top 10
            
            categories.forEach(([category, count]) => {
                const percentage = ((count / structure.total_urls) * 100).toFixed(1);
                html += `
                    <div class="flex items-center gap-2">
                        <span class="text-sm text-gray-600 w-32 truncate">${UI.escapeHtml(category)}</span>
                        <div class="flex-1 bg-gray-200 rounded-full h-2">
                            <div class="bg-primary h-2 rounded-full" style="width: ${percentage}%"></div>
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
        document.getElementById('urls-validation-results').classList.add('hidden');
        document.getElementById('urls-structure-preview').classList.add('hidden');
    }

    // Lifecycle methods
    onTabActivated() {
        // Load URLs when tab is first activated
        if (!this.urls) {
            this.loadUrls();
        }
    }

    onTabDeactivated() {
        // Nothing to clean up
    }
}
