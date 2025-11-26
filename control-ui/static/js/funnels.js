class FunnelsManager {
    constructor() {
        this.funnels = [];
        this.selectedFunnelId = null;
        this.currentFunnel = null;
        this.stepTemplates = {
            pageview: () => ({
                type: 'pageview',
                url: '',
                action_name: '',
                delay_seconds_min: 0,
                delay_seconds_max: 2,
            }),
            event: () => ({
                type: 'event',
                url: '',
                action_name: '',
                event_category: '',
                event_action: '',
                event_name: '',
                event_value: null,
                delay_seconds_min: 1,
                delay_seconds_max: 3,
            }),
            site_search: () => ({
                type: 'site_search',
                url: '',
                search_keyword: '',
                search_category: '',
                search_results: null,
                action_name: '',
                delay_seconds_min: 1,
                delay_seconds_max: 2,
            }),
            outlink: () => ({
                type: 'outlink',
                url: '',
                target_url: '',
                action_name: '',
                delay_seconds_min: 1,
                delay_seconds_max: 2,
            }),
            download: () => ({
                type: 'download',
                url: '',
                target_url: '',
                action_name: '',
                delay_seconds_min: 1,
                delay_seconds_max: 2,
            }),
            ecommerce: () => ({
                type: 'ecommerce',
                url: '',
                action_name: '',
                ecommerce_revenue: null,
                ecommerce_subtotal: null,
                ecommerce_tax: null,
                ecommerce_shipping: null,
                ecommerce_currency: null,
                delay_seconds_min: 1,
                delay_seconds_max: 2,
            }),
        };

        this.templates = {
            ecommerce: {
                name: 'Ecommerce Purchase',
                description: 'Landing → product → cart → order completion',
                probability: 0.35,
                priority: 0,
                enabled: true,
                exit_after_completion: true,
                steps: [
                    {
                        type: 'pageview',
                        url: 'https://store.example.com/',
                        action_name: 'Landing Page',
                        delay_seconds_min: 0,
                        delay_seconds_max: 2,
                    },
                    {
                        type: 'event',
                        url: 'https://store.example.com/',
                        event_category: 'CTA',
                        event_action: 'Click',
                        event_name: 'Hero CTA',
                        action_name: 'CTA Click',
                        delay_seconds_min: 1,
                        delay_seconds_max: 3,
                    },
                    {
                        type: 'pageview',
                        url: 'https://store.example.com/product/widget',
                        action_name: 'Product Detail',
                        delay_seconds_min: 2,
                        delay_seconds_max: 4,
                    },
                    {
                        type: 'event',
                        url: 'https://store.example.com/product/widget',
                        event_category: 'Product',
                        event_action: 'AddToCart',
                        event_name: 'Widget',
                        action_name: 'Add to Cart',
                        delay_seconds_min: 1,
                        delay_seconds_max: 2,
                    },
                    {
                        type: 'pageview',
                        url: 'https://store.example.com/checkout',
                        action_name: 'Checkout',
                        delay_seconds_min: 1,
                        delay_seconds_max: 3,
                    },
                    {
                        type: 'ecommerce',
                        url: 'https://store.example.com/order/complete',
                        action_name: 'Order Complete',
                        delay_seconds_min: 1,
                        delay_seconds_max: 2,
                    },
                ],
            },
            lead: {
                name: 'Lead Generation',
                description: 'Blog → resource → signup form submission',
                probability: 0.25,
                priority: 1,
                enabled: true,
                exit_after_completion: true,
                steps: [
                    {
                        type: 'pageview',
                        url: 'https://example.com/blog/marketing-trends',
                        action_name: 'Blog Post',
                        delay_seconds_min: 0,
                        delay_seconds_max: 2,
                    },
                    {
                        type: 'outlink',
                        url: 'https://example.com/blog/marketing-trends',
                        target_url: 'https://example.com/resources/marketing-guide.pdf',
                        action_name: 'Download Guide',
                        delay_seconds_min: 1,
                        delay_seconds_max: 2,
                    },
                    {
                        type: 'pageview',
                        url: 'https://example.com/resources/marketing-guide',
                        action_name: 'Resource Landing',
                        delay_seconds_min: 2,
                        delay_seconds_max: 3,
                    },
                    {
                        type: 'event',
                        url: 'https://example.com/resources/marketing-guide',
                        event_category: 'Form',
                        event_action: 'Submit',
                        event_name: 'Lead Capture',
                        action_name: 'Form Submission',
                        delay_seconds_min: 1,
                        delay_seconds_max: 2,
                    },
                ],
            },
            content: {
                name: 'Content Discovery',
                description: 'Landing → search → article reading',
                probability: 0.4,
                priority: 2,
                enabled: true,
                exit_after_completion: false,
                steps: [
                    {
                        type: 'pageview',
                        url: 'https://example.com/',
                        action_name: 'Homepage',
                        delay_seconds_min: 0,
                        delay_seconds_max: 2,
                    },
                    {
                        type: 'site_search',
                        url: 'https://example.com/',
                        search_keyword: 'analytics',
                        search_category: 'Resources',
                        search_results: 12,
                        action_name: 'Search: analytics',
                        delay_seconds_min: 1,
                        delay_seconds_max: 2,
                    },
                    {
                        type: 'pageview',
                        url: 'https://example.com/blog/analytics-best-practices',
                        action_name: 'Blog Article',
                        delay_seconds_min: 3,
                        delay_seconds_max: 6,
                    },
                    {
                        type: 'event',
                        url: 'https://example.com/blog/analytics-best-practices',
                        event_category: 'Engagement',
                        event_action: 'ScrollDepth',
                        event_name: '75%',
                        action_name: 'Scroll Depth',
                        delay_seconds_min: 1,
                        delay_seconds_max: 2,
                    },
                ],
            },
        };
    }

    init() {
        this.listContainer = document.getElementById('funnels-list');
        this.templateSelect = document.getElementById('funnel-template-select');
        this.nameInput = document.getElementById('funnel-name');
        this.descriptionInput = document.getElementById('funnel-description');
        this.probabilityInput = document.getElementById('funnel-probability');
        this.priorityInput = document.getElementById('funnel-priority');
        this.enabledCheckbox = document.getElementById('funnel-enabled');
        this.exitAfterCheckbox = document.getElementById('funnel-exit-after');
        this.stepsContainer = document.getElementById('funnel-steps-container');
        this.previewPanel = document.getElementById('funnel-preview');
        this.previewContent = document.getElementById('funnel-preview-content');
        this.editorTitle = document.getElementById('funnel-editor-title');
        this.editorSubtitle = document.getElementById('funnel-editor-subtitle');

        document.getElementById('create-funnel-btn').addEventListener('click', () => this.startNewFunnel());
        document.getElementById('add-step-btn').addEventListener('click', () => this.addStep());
        document.getElementById('save-funnel-btn').addEventListener('click', () => this.saveFunnel());
        document.getElementById('preview-funnel-btn').addEventListener('click', () => this.previewFunnel());
        this.templateSelect.addEventListener('change', (e) => this.applyTemplate(e.target.value));

        this.stepsContainer.addEventListener('input', (event) => this.handleStepInput(event));
        this.stepsContainer.addEventListener('click', (event) => this.handleStepActions(event));

        this.startNewFunnel();
    }

    onTabActivated() {
        this.loadFunnels();
    }

    onTabDeactivated() {
        if (this.previewPanel) {
            this.previewPanel.classList.add('hidden');
        }
    }

    async loadFunnels() {
        try {
            const response = await api.getFunnels();
            this.funnels = response.funnels || [];
            this.renderFunnelsList();
        } catch (error) {
            console.error('Failed to load funnels', error);
            UI.showAlert(`Failed to load funnels: ${error.message}`, 'error');
        }
    }

    renderFunnelsList() {
        if (!this.listContainer) return;

        if (!this.funnels.length) {
            this.listContainer.innerHTML = `
                <div class="p-6 text-sm text-gray-500 text-center">
                    No funnels defined yet. Click "New Funnel" to create one.
                </div>
            `;
            return;
        }

        this.listContainer.innerHTML = this.funnels
            .map((funnel) => {
                const active = this.selectedFunnelId === funnel.id;
                return `
                    <div class="p-4 cursor-pointer hover:bg-gray-50 ${active ? 'bg-blue-50 border-l-4 border-primary' : ''}" data-funnel-id="${funnel.id}">
                        <div class="flex items-start justify-between gap-2">
                            <div>
                                <h3 class="text-sm font-semibold text-gray-900">${funnel.name}</h3>
                                <p class="text-xs text-gray-500 mt-1">${funnel.description || 'No description provided.'}</p>
                                <div class="mt-2 flex flex-wrap items-center gap-3 text-xs text-gray-500">
                                    <span>Priority: ${funnel.priority}</span>
                                    <span>Probability: ${(funnel.probability * 100).toFixed(1)}%</span>
                                    <span>${funnel.enabled ? 'Enabled' : 'Disabled'}</span>
                                    <span>${funnel.step_count} step${funnel.step_count === 1 ? '' : 's'}</span>
                                </div>
                            </div>
                            <div class="flex flex-col gap-2">
                                <button class="text-xs text-primary hover:underline" data-action="edit" data-funnel-id="${funnel.id}">Edit</button>
                                <button class="text-xs text-gray-500 hover:text-primary" data-action="duplicate" data-funnel-id="${funnel.id}">Duplicate</button>
                                <button class="text-xs text-red-500 hover:text-red-600" data-action="delete" data-funnel-id="${funnel.id}">Delete</button>
                            </div>
                        </div>
                    </div>
                `;
            })
            .join('');

        this.listContainer.querySelectorAll('[data-funnel-id]').forEach((element) => {
            element.addEventListener('click', (event) => {
                const target = event.target.closest('[data-action]');
                const id = parseInt(element.getAttribute('data-funnel-id'), 10);
                if (!Number.isInteger(id)) return;

                if (target) {
                    event.stopPropagation();
                    const action = target.getAttribute('data-action');
                    if (action === 'edit') {
                        this.selectFunnel(id);
                    } else if (action === 'delete') {
                        this.deleteFunnel(id);
                    } else if (action === 'duplicate') {
                        this.duplicateFunnel(id);
                    }
                } else {
                    this.selectFunnel(id);
                }
            });
        });
    }

    async selectFunnel(funnelId) {
        try {
            UI.showLoading('Loading funnel...');
            const funnel = await api.getFunnel(funnelId);
            UI.hideLoading();
            this.selectedFunnelId = funnelId;
            this.setEditorState(funnel);
            this.renderFunnelsList();
        } catch (error) {
            UI.hideLoading();
            UI.showAlert(`Failed to load funnel: ${error.message}`, 'error');
        }
    }

    startNewFunnel(template) {
        this.selectedFunnelId = null;
        this.currentFunnel = template ? this.cloneFunnel(template) : this.blankFunnel();
        this.setEditorState(this.currentFunnel);
        this.renderFunnelsList();
    }

    blankFunnel() {
        return {
            name: 'New Funnel',
            description: '',
            probability: 0.2,
            priority: 0,
            enabled: true,
            config: {
                probability: 0.2,
                priority: 0,
                enabled: true,
                exit_after_completion: true,
                steps: [this.stepTemplates.pageview()],
            },
            created_at: '',
            updated_at: '',
        };
    }

    setEditorState(funnel) {
        this.currentFunnel = this.cloneFunnel(funnel);
        const config = this.currentFunnel.config || {
            probability: funnel.probability ?? 0,
            priority: funnel.priority ?? 0,
            enabled: funnel.enabled ?? true,
            exit_after_completion: funnel.exit_after_completion ?? true,
            steps: [],
        };

        this.editorTitle.textContent = this.selectedFunnelId ? 'Edit Funnel' : 'Create Funnel';
        this.editorSubtitle.textContent = this.selectedFunnelId
            ? `Editing: ${funnel.name}`
            : 'Define multi-step journeys with delays, events, and conversions.';

        this.nameInput.value = funnel.name || '';
        this.descriptionInput.value = funnel.description || '';
        this.probabilityInput.value = config.probability ?? funnel.probability ?? 0;
        this.priorityInput.value = config.priority ?? funnel.priority ?? 0;
        this.enabledCheckbox.checked = config.enabled ?? funnel.enabled ?? true;
        this.exitAfterCheckbox.checked = config.exit_after_completion ?? true;

        this.steps = (config.steps || []).map((step) => ({ ...this.stepTemplates[step.type]?.(), ...step }));
        if (!this.steps.length) {
            this.steps.push(this.stepTemplates.pageview());
        }
        this.renderSteps();
        this.previewPanel.classList.add('hidden');
        this.previewContent.innerHTML = '';
    }

    cloneFunnel(funnel) {
        const config = funnel.config || {};
        return {
            id: funnel.id ?? null,
            name: funnel.name ?? '',
            description: funnel.description ?? '',
            probability: funnel.probability ?? config.probability ?? 0,
            priority: funnel.priority ?? config.priority ?? 0,
            enabled: funnel.enabled ?? config.enabled ?? true,
            created_at: funnel.created_at ?? '',
            updated_at: funnel.updated_at ?? '',
            config: {
                probability: config.probability ?? funnel.probability ?? 0,
                priority: config.priority ?? funnel.priority ?? 0,
                enabled: config.enabled ?? funnel.enabled ?? true,
                exit_after_completion: config.exit_after_completion ?? true,
                steps: Array.isArray(config.steps)
                    ? config.steps.map((step) => ({ ...step }))
                    : [],
            },
        };
    }

    renderSteps() {
        if (!this.stepsContainer) return;

        if (!this.steps.length) {
            this.stepsContainer.innerHTML = `<div class="text-sm text-gray-500">No steps yet. Click "Add Step" to begin.</div>`;
            return;
        }

        this.stepsContainer.innerHTML = this.steps
            .map((step, index) => {
                const indexLabel = index + 1;
                return `
                    <div class="border border-gray-200 rounded-lg p-4 bg-white shadow-sm" data-step-index="${index}">
                        <div class="flex items-center justify-between mb-3">
                            <div>
                                <h4 class="text-sm font-semibold text-gray-900">Step ${indexLabel}</h4>
                                <p class="text-xs text-gray-500">${step.type.replace('_', ' ').toUpperCase()}</p>
                            </div>
                            <div class="flex items-center gap-2">
                                <button class="text-xs text-gray-500 hover:text-primary" data-step-action="move-up" ${index === 0 ? 'disabled' : ''}>Up</button>
                                <button class="text-xs text-gray-500 hover:text-primary" data-step-action="move-down" ${index === this.steps.length - 1 ? 'disabled' : ''}>Down</button>
                                <button class="text-xs text-gray-500 hover:text-primary" data-step-action="duplicate">Duplicate</button>
                                <button class="text-xs text-red-500 hover:text-red-600" data-step-action="remove">Remove</button>
                            </div>
                        </div>

                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label class="block text-xs font-medium text-gray-600 mb-1">Step Type</label>
                                <select class="step-input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                                    data-field="type" data-step-index="${index}">
                                    ${Object.keys(this.stepTemplates)
                                        .map(
                                            (type) =>
                                                `<option value="${type}" ${step.type === type ? 'selected' : ''}>${type.replace('_', ' ')}</option>`
                                        )
                                        .join('')}
                                </select>
                            </div>
                            <div data-field-group="url" class="${['pageview', 'event', 'site_search', 'outlink', 'download', 'ecommerce'].includes(step.type) ? '' : 'hidden'}">
                                <label class="block text-xs font-medium text-gray-600 mb-1">Page URL</label>
                                <input type="text" class="step-input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                                    data-field="url" data-step-index="${index}" value="${step.url ?? ''}" placeholder="https://example.com/page">
                            </div>
                            <div data-field-group="action_name" class="col-span-1 md:col-span-2 ${['pageview', 'event', 'outlink', 'download', 'ecommerce', 'site_search'].includes(step.type) ? '' : 'hidden'}">
                                <label class="block text-xs font-medium text-gray-600 mb-1">Action Name (optional)</label>
                                <input type="text" class="step-input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                                    data-field="action_name" data-step-index="${index}" value="${step.action_name ?? ''}" placeholder="Display name in Matomo reports">
                            </div>

                            <div data-field-group="event" class="${step.type === 'event' ? '' : 'hidden'}">
                                <label class="block text-xs font-medium text-gray-600 mb-1">Event Category</label>
                                <input type="text" class="step-input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                                    data-field="event_category" data-step-index="${index}" value="${step.event_category ?? ''}" placeholder="e.g., CTA">
                            </div>
                            <div data-field-group="event" class="${step.type === 'event' ? '' : 'hidden'}">
                                <label class="block text-xs font-medium text-gray-600 mb-1">Event Action</label>
                                <input type="text" class="step-input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus-border-transparent"
                                    data-field="event_action" data-step-index="${index}" value="${step.event_action ?? ''}" placeholder="e.g., Click">
                            </div>
                            <div data-field-group="event" class="col-span-1 md:col-span-2 ${step.type === 'event' ? '' : 'hidden'}">
                                <label class="block text-xs font-medium text-gray-600 mb-1">Event Name</label>
                                <input type="text" class="step-input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus-border-transparent"
                                    data-field="event_name" data-step-index="${index}" value="${step.event_name ?? ''}" placeholder="e.g., Hero CTA">
                            </div>
                            <div data-field-group="event" class="${step.type === 'event' ? '' : 'hidden'}">
                                <label class="block text-xs font-medium text-gray-600 mb-1">Event Value</label>
                                <input type="number" step="0.01" class="step-input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus-border-transparent"
                                    data-field="event_value" data-step-index="${index}" value="${step.event_value ?? ''}" placeholder="Optional numeric value">
                            </div>

                            <div data-field-group="search" class="${step.type === 'site_search' ? '' : 'hidden'}">
                                <label class="block text-xs font-medium text-gray-600 mb-1">Search Keyword</label>
                                <input type="text" class="step-input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus-border-transparent"
                                    data-field="search_keyword" data-step-index="${index}" value="${step.search_keyword ?? ''}" placeholder="analytics">
                            </div>
                            <div data-field-group="search" class="${step.type === 'site_search' ? '' : 'hidden'}">
                                <label class="block text-xs font-medium text-gray-600 mb-1">Search Category</label>
                                <input type="text" class="step-input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus-border-transparent"
                                    data-field="search_category" data-step-index="${index}" value="${step.search_category ?? ''}" placeholder="Optional category">
                            </div>
                            <div data-field-group="search" class="${step.type === 'site_search' ? '' : 'hidden'}">
                                <label class="block text-xs font-medium text-gray-600 mb-1">Search Results</label>
                                <input type="number" class="step-input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus-border-transparent"
                                    data-field="search_results" data-step-index="${index}" value="${step.search_results ?? ''}" placeholder="Optional result count">
                            </div>

                            <div data-field-group="target" class="${['outlink', 'download'].includes(step.type) ? '' : 'hidden'}">
                                <label class="block text-xs font-medium text-gray-600 mb-1">Target URL</label>
                                <input type="text" class="step-input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus-border-transparent"
                                    data-field="target_url" data-step-index="${index}" value="${step.target_url ?? ''}" placeholder="https://external-site.com">
                            </div>

                            <div data-field-group="ecommerce" class="${step.type === 'ecommerce' ? '' : 'hidden'}">
                                <label class="block text-xs font-medium text-gray-600 mb-1">Revenue Override</label>
                                <input type="number" step="0.01" class="step-input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus-border-transparent"
                                    data-field="ecommerce_revenue" data-step-index="${index}" value="${step.ecommerce_revenue ?? ''}" placeholder="Optional revenue">
                            </div>
                            <div data-field-group="ecommerce" class="${step.type === 'ecommerce' ? '' : 'hidden'}">
                                <label class="block text-xs font-medium text-gray-600 mb-1">Currency</label>
                                <input type="text" maxlength="3" class="step-input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus-border-transparent"
                                    data-field="ecommerce_currency" data-step-index="${index}" value="${step.ecommerce_currency ?? ''}" placeholder="e.g., SEK">
                            </div>

                            <div>
                                <label class="block text-xs font-medium text-gray-600 mb-1">Delay Min (seconds)</label>
                                <input type="number" step="0.1" min="0" class="step-input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus-border-transparent"
                                    data-field="delay_seconds_min" data-step-index="${index}" value="${step.delay_seconds_min ?? 0}">
                            </div>
                            <div>
                                <label class="block text-xs font-medium text-gray-600 mb-1">Delay Max (seconds)</label>
                                <input type="number" step="0.1" min="0" class="step-input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus-border-transparent"
                                    data-field="delay_seconds_max" data-step-index="${index}" value="${step.delay_seconds_max ?? step.delay_seconds_min ?? 0}">
                            </div>
                        </div>
                    </div>
                `;
            })
            .join('');
    }

    handleStepInput(event) {
        const input = event.target;
        if (!input.classList.contains('step-input')) return;

        const index = parseInt(input.dataset.stepIndex, 10);
        const field = input.dataset.field;
        if (!Number.isInteger(index) || !field || !this.steps[index]) return;

        const value = input.value === '' ? null : input.value;
        const step = this.steps[index];

        if (field === 'type') {
            const existing = this.stepTemplates[value]?.();
            if (existing) {
                const preserved = {
                    url: step.url,
                    action_name: step.action_name,
                };
                this.steps[index] = { ...existing, ...preserved, type: value };
                this.renderSteps();
            }
            return;
        }

        if (['delay_seconds_min', 'delay_seconds_max', 'event_value', 'search_results', 'ecommerce_revenue', 'ecommerce_subtotal', 'ecommerce_tax', 'ecommerce_shipping'].includes(field)) {
            this.steps[index][field] = value === null ? null : parseFloat(value);
        } else if (field === 'search_results') {
            this.steps[index][field] = value === null ? null : parseInt(value, 10);
        } else {
            this.steps[index][field] = value;
        }
    }

    handleStepActions(event) {
        const button = event.target.closest('[data-step-action]');
        if (!button) return;

        const action = button.dataset.stepAction;
        const stepElement = button.closest('[data-step-index]');
        if (!stepElement) return;
        const index = parseInt(stepElement.dataset.stepIndex, 10);
        if (!Number.isInteger(index)) return;

        event.preventDefault();
        event.stopPropagation();

        if (action === 'remove') {
            this.steps.splice(index, 1);
            if (!this.steps.length) {
                this.steps.push(this.stepTemplates.pageview());
            }
            this.renderSteps();
        } else if (action === 'move-up' && index > 0) {
            [this.steps[index - 1], this.steps[index]] = [this.steps[index], this.steps[index - 1]];
            this.renderSteps();
        } else if (action === 'move-down' && index < this.steps.length - 1) {
            [this.steps[index + 1], this.steps[index]] = [this.steps[index], this.steps[index + 1]];
            this.renderSteps();
        } else if (action === 'duplicate') {
            const clone = JSON.parse(JSON.stringify(this.steps[index]));
            this.steps.splice(index + 1, 0, clone);
            this.renderSteps();
        }
    }

    addStep(type = 'pageview') {
        const template = this.stepTemplates[type] ? this.stepTemplates[type]() : this.stepTemplates.pageview();
        this.steps.push(template);
        this.renderSteps();
    }

    previewFunnel() {
        if (!this.previewPanel || !this.previewContent) return;

        const payload = this.collectFormPayload(false);
        if (!payload) return;

        const steps = payload.steps || [];
        if (!steps.length) {
            UI.showAlert('Add at least one step before previewing.', 'warning');
            return;
        }

        const lines = steps.map((step, index) => {
            const label = `${index + 1}. ${step.type.replace('_', ' ').toUpperCase()}`;
            const url = step.url ? `• ${step.url}` : '';
            const action = step.action_name ? `• ${step.action_name}` : '';
            const delay = `• delay ${step.delay_seconds_min ?? 0}-${step.delay_seconds_max ?? 0}s`;
            return `<div class="flex flex-col gap-1">
                <div class="font-medium text-gray-800">${label}</div>
                <div class="text-xs text-gray-500 space-x-2">
                    ${url ? `<span>${url}</span>` : ''}
                    ${action ? `<span>${action}</span>` : ''}
                    <span>${delay}</span>
                </div>
            </div>`;
        });

        this.previewContent.innerHTML = lines.join('<hr class="my-2 border-gray-200">');
        this.previewPanel.classList.remove('hidden');
    }

    collectFormPayload(requireSteps = true) {
        const name = this.nameInput.value.trim();
        if (!name) {
            UI.showAlert('Please provide a funnel name.', 'warning');
            return null;
        }

        const probability = parseFloat(this.probabilityInput.value);
        if (Number.isNaN(probability) || probability < 0 || probability > 1) {
            UI.showAlert('Probability must be between 0 and 1.', 'warning');
            return null;
        }

        const priority = parseInt(this.priorityInput.value || '0', 10);
        if (Number.isNaN(priority) || priority < 0) {
            UI.showAlert('Priority must be 0 or greater.', 'warning');
            return null;
        }

        const steps = (this.steps || []).map((step) => {
            const sanitized = { ...step };
            if (sanitized.delay_seconds_max < sanitized.delay_seconds_min) {
                sanitized.delay_seconds_max = sanitized.delay_seconds_min;
            }
            return sanitized;
        });

        if (requireSteps && !steps.length) {
            UI.showAlert('Funnels require at least one step.', 'warning');
            return null;
        }

        return {
            name,
            description: this.descriptionInput.value.trim(),
            probability,
            priority,
            enabled: this.enabledCheckbox.checked,
            exit_after_completion: this.exitAfterCheckbox.checked,
            steps,
        };
    }

    async saveFunnel() {
        const payload = this.collectFormPayload();
        if (!payload) return;

        try {
            UI.showLoading('Saving funnel...');
            if (this.selectedFunnelId) {
                await api.updateFunnel(this.selectedFunnelId, payload);
                UI.showAlert('Funnel updated successfully!', 'success');
            } else {
                const created = await api.createFunnel(payload);
                this.selectedFunnelId = created.id;
                UI.showAlert('Funnel created successfully!', 'success');
            }
            await this.loadFunnels();
            if (this.selectedFunnelId) {
                await this.selectFunnel(this.selectedFunnelId);
            }
        } catch (error) {
            UI.showAlert(`Failed to save funnel: ${error.message}`, 'error');
        } finally {
            UI.hideLoading();
        }
    }

    async deleteFunnel(funnelId) {
        const funnel = this.funnels.find((f) => f.id === funnelId);
        const name = funnel ? funnel.name : 'this funnel';
        if (!confirm(`Delete ${name}? This action cannot be undone.`)) {
            return;
        }

        try {
            UI.showLoading('Deleting funnel...');
            await api.deleteFunnel(funnelId);
            UI.showAlert('Funnel deleted successfully.', 'success');
            if (this.selectedFunnelId === funnelId) {
                this.startNewFunnel();
            }
            await this.loadFunnels();
        } catch (error) {
            UI.showAlert(`Failed to delete funnel: ${error.message}`, 'error');
        } finally {
            UI.hideLoading();
        }
    }

    async duplicateFunnel(funnelId) {
        try {
            UI.showLoading('Duplicating funnel...');
            const detail = await api.getFunnel(funnelId);
            UI.hideLoading();
            const clone = this.cloneFunnel({
                ...detail,
                id: null,
                name: `${detail.name} Copy`,
            });
            this.startNewFunnel(clone);
        } catch (error) {
            UI.hideLoading();
            UI.showAlert(`Failed to duplicate funnel: ${error.message}`, 'error');
        }
    }

    applyTemplate(templateKey) {
        if (!templateKey || !this.templates[templateKey]) return;
        const template = this.cloneFunnel({
            ...this.templates[templateKey],
            id: null,
            config: {
                probability: this.templates[templateKey].probability,
                priority: this.templates[templateKey].priority,
                enabled: this.templates[templateKey].enabled,
                exit_after_completion: this.templates[templateKey].exit_after_completion,
                steps: (this.templates[templateKey].steps || []).map((step) => ({ ...step })),
            },
        });
        this.startNewFunnel(template);
        this.templateSelect.value = '';
    }
}

window.FunnelsManager = FunnelsManager;
