// Multi-Target Configuration Management (P-008)
class MultiTargetManager {
    constructor() {
        this.targets = [];
        this.nextTargetId = 1;
        this.isMultiTargetMode = false;
    }

    // Initialize multi-target UI
    init() {
        this.setupEventListeners();
        this.checkMode();
    }

    // Setup event listeners
    setupEventListeners() {
        // Mode toggle
        const modeToggle = document.getElementById('multi-target-mode');
        if (modeToggle) {
            modeToggle.addEventListener('change', (e) => {
                this.toggleMode(e.target.checked);
            });
        }

        // Add target button
        const addBtn = document.getElementById('add-target-btn');
        if (addBtn) {
            addBtn.addEventListener('click', () => this.addTarget());
        }

        // Distribution strategy change
        const strategySelect = document.getElementById('distribution_strategy');
        if (strategySelect) {
            strategySelect.addEventListener('change', (e) => {
                this.handleStrategyChange(e.target.value);
            });
        }

        // Test all targets button
        const testAllBtn = document.getElementById('test-all-targets-btn');
        if (testAllBtn) {
            testAllBtn.addEventListener('click', () => this.testAllTargets());
        }
    }

    // Check which mode is active based on form data
    checkMode() {
        const singleTargetContainer = document.getElementById('single-target-config');
        const multiTargetContainer = document.getElementById('multi-target-config');
        const modeToggle = document.getElementById('multi-target-mode');

        // Check if we have target data in the form
        const targetsContainer = document.getElementById('targets-container');
        const hasTargets = targetsContainer && targetsContainer.children.length > 0;

        if (hasTargets) {
            // Already in multi-target mode
            this.isMultiTargetMode = true;
            if (modeToggle) modeToggle.checked = true;
            if (singleTargetContainer) singleTargetContainer.classList.add('hidden');
            if (multiTargetContainer) multiTargetContainer.classList.remove('hidden');
        } else {
            // Single-target mode
            this.isMultiTargetMode = false;
            if (modeToggle) modeToggle.checked = false;
            if (singleTargetContainer) singleTargetContainer.classList.remove('hidden');
            if (multiTargetContainer) multiTargetContainer.classList.add('hidden');
        }
    }

    // Toggle between single and multi-target mode
    toggleMode(enableMultiTarget) {
        const singleTargetContainer = document.getElementById('single-target-config');
        const multiTargetContainer = document.getElementById('multi-target-config');
        const testConnectionBtn = document.getElementById('test-connection-btn');
        const validateBtn = document.getElementById('validate-config-btn');

        this.isMultiTargetMode = enableMultiTarget;

        if (enableMultiTarget) {
            // Convert single target to multi-target
            singleTargetContainer.classList.add('hidden');
            multiTargetContainer.classList.remove('hidden');
            
            // Hide single-target test button, keep validate visible
            if (testConnectionBtn) testConnectionBtn.classList.add('hidden');

            // If no targets exist, create one from single-target fields
            if (this.targets.length === 0) {
                const singleUrl = document.getElementById('matomo_url')?.value;
                const singleSiteId = document.getElementById('matomo_site_id')?.value;
                const singleToken = document.getElementById('matomo_token_auth')?.value;

                if (singleUrl && singleSiteId) {
                    this.addTarget({
                        name: 'Primary Target',
                        url: singleUrl,
                        site_id: parseInt(singleSiteId),
                        token_auth: singleToken || '',
                        weight: 100,
                        enabled: true
                    });
                } else {
                    // Add empty target
                    this.addTarget();
                }
            }
        } else {
            // Convert multi-target to single-target
            multiTargetContainer.classList.add('hidden');
            singleTargetContainer.classList.remove('hidden');
            
            // Show single-target test button again
            if (testConnectionBtn) testConnectionBtn.classList.remove('hidden');

            // Copy first enabled target to single-target fields
            if (this.targets.length > 0) {
                const firstTarget = this.targets.find(t => t.enabled) || this.targets[0];
                if (firstTarget) {
                    document.getElementById('matomo_url').value = firstTarget.url || '';
                    document.getElementById('matomo_site_id').value = firstTarget.site_id || '';
                    document.getElementById('matomo_token_auth').value = firstTarget.token_auth || '';
                }
            }

            // Clear multi-target data
            this.targets = [];
            this.renderTargets();
        }
    }

    // Add a new target
    addTarget(targetData = null) {
        const target = targetData || {
            id: this.nextTargetId++,
            name: `Target ${this.targets.length + 1}`,
            url: '',
            site_id: 1,
            token_auth: '',
            weight: 50,
            enabled: true
        };

        if (!target.id) {
            target.id = this.nextTargetId++;
        }

        this.targets.push(target);
        this.renderTargets();
    }

    // Remove a target
    removeTarget(targetId) {
        if (this.targets.length <= 1) {
            UI.showAlert('At least one target is required in multi-target mode', 'warning');
            return;
        }

        UI.confirm(
            'Remove this target? This cannot be undone.',
            () => {
                this.targets = this.targets.filter(t => t.id !== targetId);
                this.renderTargets();
            }
        );
    }

    // Render all targets
    renderTargets() {
        const container = document.getElementById('targets-container');
        if (!container) return;

        container.innerHTML = '';

        this.targets.forEach((target, index) => {
            container.appendChild(this.createTargetCard(target, index));
        });
    }

    // Create a target configuration card
    createTargetCard(target, index) {
        const card = document.createElement('div');
        card.className = 'border border-gray-300 rounded-lg p-4 bg-white';
        card.dataset.targetId = target.id;

        const strategyValue = document.getElementById('distribution_strategy')?.value || 'round-robin';
        const showWeight = strategyValue === 'weighted';

        card.innerHTML = `
            <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-3">
                    <input type="checkbox" 
                           class="target-enabled w-4 h-4 text-primary rounded focus:ring-primary" 
                           ${target.enabled ? 'checked' : ''}>
                    <h4 class="text-sm font-semibold text-gray-900">Target ${index + 1}</h4>
                </div>
                <button type="button" class="remove-target-btn text-red-600 hover:text-red-800">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                    </svg>
                </button>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="form-group">
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Name <span class="text-red-500">*</span>
                    </label>
                    <input type="text" class="target-name w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary" 
                           value="${UI.escapeHtml(target.name)}" required>
                    <p class="text-xs text-gray-500 mt-1">Human-friendly label</p>
                </div>

                <div class="form-group">
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        URL <span class="text-red-500">*</span>
                    </label>
                    <input type="url" class="target-url w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary" 
                           value="${UI.escapeHtml(target.url)}" placeholder="https://matomo.example.com" required>
                    <p class="text-xs text-gray-500 mt-1">Matomo tracking endpoint</p>
                </div>

                <div class="form-group">
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Site ID <span class="text-red-500">*</span>
                    </label>
                    <input type="number" class="target-site-id w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary" 
                           value="${target.site_id}" min="1" required>
                </div>

                <div class="form-group">
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Token Auth (Optional)
                    </label>
                    <input type="password" class="target-token w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary" 
                           value="${UI.escapeHtml(target.token_auth || '')}" placeholder="••••••••••••••••">
                </div>

                ${showWeight ? `
                <div class="form-group">
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Weight <span class="text-red-500">*</span>
                    </label>
                    <input type="number" class="target-weight w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary" 
                           value="${target.weight}" min="1" max="100" required>
                    <p class="text-xs text-gray-500 mt-1">Distribution weight (1-100)</p>
                </div>
                ` : ''}
            </div>
        `;

        // Add event listeners
        const enabledCheckbox = card.querySelector('.target-enabled');
        enabledCheckbox.addEventListener('change', (e) => {
            target.enabled = e.target.checked;
        });

        const removeBtn = card.querySelector('.remove-target-btn');
        removeBtn.addEventListener('click', () => this.removeTarget(target.id));

        // Update target data on input
        const inputs = {
            name: card.querySelector('.target-name'),
            url: card.querySelector('.target-url'),
            site_id: card.querySelector('.target-site-id'),
            token_auth: card.querySelector('.target-token'),
            weight: card.querySelector('.target-weight')
        };

        Object.entries(inputs).forEach(([field, input]) => {
            if (!input) return;
            input.addEventListener('input', (e) => {
                if (field === 'site_id' || field === 'weight') {
                    target[field] = parseInt(e.target.value) || 0;
                } else {
                    target[field] = e.target.value;
                }
            });
        });

        return card;
    }

    // Handle distribution strategy change
    handleStrategyChange(strategy) {
        // Re-render to show/hide weight fields
        this.renderTargets();
    }

    // Get multi-target configuration for API
    getMultiTargetConfig() {
        if (!this.isMultiTargetMode || this.targets.length === 0) {
            return null;
        }

        const strategySelect = document.getElementById('distribution_strategy');
        const strategy = strategySelect ? strategySelect.value : 'round-robin';

        return {
            targets: this.targets.map(t => ({
                name: t.name,
                url: t.url,
                site_id: parseInt(t.site_id),
                token_auth: t.token_auth || null,
                weight: parseInt(t.weight) || 1,
                enabled: t.enabled
            })),
            distribution_strategy: strategy
        };
    }

    // Load multi-target configuration
    loadMultiTargetConfig(config) {
        if (!config || !config.targets || config.targets.length === 0) {
            return;
        }

        // Enable multi-target mode
        const modeToggle = document.getElementById('multi-target-mode');
        if (modeToggle) {
            modeToggle.checked = true;
        }
        this.toggleMode(true);

        // Load targets
        this.targets = config.targets.map((t, index) => ({
            id: this.nextTargetId++,
            name: t.name || `Target ${index + 1}`,
            url: t.url,
            site_id: t.site_id,
            token_auth: t.token_auth || '',
            weight: t.weight || 50,
            enabled: t.enabled !== false
        }));

        // Load strategy
        const strategySelect = document.getElementById('distribution_strategy');
        if (strategySelect && config.distribution_strategy) {
            strategySelect.value = config.distribution_strategy;
        }

        this.renderTargets();
    }

    // Test connectivity to all targets
    async testAllTargets() {
        if (!this.isMultiTargetMode || this.targets.length === 0) {
            UI.showAlert('No targets to test', 'warning');
            return;
        }

        UI.showLoading('Testing all targets...');

        const results = [];
        for (const target of this.targets) {
            if (!target.enabled) continue;

            try {
                const result = await api.testConnection(target.url, target.site_id);
                results.push({
                    name: target.name,
                    success: result.success,
                    latency: result.response_time_ms,
                    error: result.error || result.message
                });
            } catch (error) {
                results.push({
                    name: target.name,
                    success: false,
                    latency: null,
                    error: error.message
                });
            }
        }

        UI.hideLoading();

        // Show results dialog
        this.showTestResults(results);
    }

    // Show test results in a dialog
    showTestResults(results) {
        const successCount = results.filter(r => r.success).length;
        const totalCount = results.length;

        const resultRows = results.map(r => {
            const statusIcon = r.success 
                ? '<svg class="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path></svg>'
                : '<svg class="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path></svg>';

            return `
                <tr>
                    <td class="px-4 py-3 flex items-center gap-2">
                        ${statusIcon}
                        <span class="font-medium">${UI.escapeHtml(r.name)}</span>
                    </td>
                    <td class="px-4 py-3 text-sm text-gray-600">
                        ${r.success ? `${r.latency}ms` : '--'}
                    </td>
                    <td class="px-4 py-3 text-sm ${r.success ? 'text-green-600' : 'text-red-600'}">
                        ${r.success ? '✓ Success' : `✗ ${UI.escapeHtml(r.error || 'Failed')}`}
                    </td>
                </tr>
            `;
        }).join('');

        const dialogHtml = `
            <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" id="test-results-dialog">
                <div class="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
                    <h3 class="text-lg font-semibold mb-4">Target Connectivity Test Results</h3>
                    
                    <div class="mb-4 p-4 ${successCount === totalCount ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'} border rounded-lg">
                        <p class="text-sm font-medium">
                            ${successCount} of ${totalCount} targets reachable
                        </p>
                    </div>

                    <table class="w-full">
                        <thead class="bg-gray-50 border-b border-gray-200">
                            <tr>
                                <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Target</th>
                                <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Latency</th>
                                <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-200">
                            ${resultRows}
                        </tbody>
                    </table>

                    <div class="flex justify-end mt-6">
                        <button id="close-test-results-btn" class="px-4 py-2 text-sm font-medium text-white bg-primary rounded-lg hover:bg-blue-700">
                            Close
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', dialogHtml);

        const dialog = document.getElementById('test-results-dialog');
        const closeBtn = document.getElementById('close-test-results-btn');

        closeBtn.addEventListener('click', () => dialog.remove());
        dialog.addEventListener('click', (e) => {
            if (e.target === dialog) dialog.remove();
        });
    }
}

// Initialize multi-target manager
window.MultiTargetManager = MultiTargetManager;
