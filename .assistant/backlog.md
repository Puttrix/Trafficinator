# Backlog

## Assistant Maintenance
- [x] **P-034** Refresh assistant status/task log
      tags: maintenance  priority: low  est: 0.1h  completed: 2026-01-07
      deps: none
      accepts: status.md reflects current backlog and task log; task_log captures the refresh entry
      result: Updated `.assistant/status.md` and appended a 2026-01-07 log entry.

## Documentation & Alignment
- [x] **P-001** Update assistant documentation to reference correct docker-compose files
      tags: documentation, maintenance  priority: medium  est: 1h  completed: 2025-10-30
      deps: none
      accepts: Assistant guide references docker-compose.yml and docker-compose.prod.yml instead of docker-compose.loadgen.yml; notes URLs are embedded in image
      result: Replaced legacy CLAUDE.md with `.assistant/ai_guidance.md` covering current compose files (dev/prod/webui) and deployment notes.

- [x] **P-002** Document embedded URLs in assistant guidance
      tags: documentation, maintenance  priority: medium  est: 0.5h  completed: 2025-10-30
      deps: P-001
      accepts: Documentation clearly states URLs are built into Docker image
      result: `.assistant/ai_guidance.md` explains that `urls.txt` ships inside the image and custom URLs are managed through the Control UI.

## Configuration Defaults
- [x] **P-030** Default timezone to CET across presets/UI
      tags: maintenance, config  priority: low  est: 0.5h  completed: 2025-11-26
      deps: none
      accepts: Presets and UI load with TIMEZONE=CET by default; loader honors CET default while allowing override.
      result: Updated loader env default to CET, Control UI defaults/placeholders, preset env files, and preset definitions.

- [x] **P-031** Default ecommerce currency to SEK (overrideable)
      tags: maintenance, ecommerce  priority: low  est: 0.5h  completed: 2025-11-26
      deps: none
      accepts: Default ecommerce currency shows as SEK while remaining user-editable; validation supports overrides and loader passes chosen currency.
      result: Set validator/UI/presets to SEK defaults and ensured loader always includes currency code.

## Testing & Quality
- [x] **P-003** Enhance test coverage for complex behaviors
      tags: testing, quality  priority: high  est: 4h  completed: 2025-10-30
      deps: none
      accepts: Tests cover events, ecommerce, daily cap, and action ordering guarantees
      result: Added pytest modules for ecommerce orders and event definitions, and updated action ordering tests to cover click/random events.

- [x] **P-004** Add validation utilities for configuration
      tags: testing, devx  priority: medium  est: 3h  completed: 2025-10-30
      deps: none
      accepts: Script validates env vars and tests Matomo connectivity before load test
      result: Introduced `tools/validate_config.py` CLI that reuses the Control UI validator to check environment variables and optionally probe Matomo connectivity.

## Features - Short Term
- [x] **P-005** Create load preset configurations (Light/Medium/Heavy)
      tags: feature, usability  priority: low  est: 2h  completed: 2025-10-30
      deps: none
      accepts: Example compose files or env templates for Light (1k/day), Medium (10k/day), Heavy (50k+/day)
      result: Added CLI-friendly presets (`presets/.env.light|medium|heavy`) plus documentation for using them with Docker Compose.

- [ ] **P-006** Improve realistic traffic patterns with user journeys
      tags: feature, realism  priority: medium  est: 6h
      deps: none
      accepts: Define and implement user journey templates (researcher, buyer, casual browser)

## Features - Mid/Long Term
- [x] **P-007** Evaluate Control UI/API feasibility
      tags: feature, webui, parked  priority: low  est: 16h  **COMPLETED: 2025-10-29**
      deps: none
      accepts: Technical feasibility study with pros/cons; see .codex/webui-parked.md
      result: Comprehensive feasibility study completed → Decision: Build Full Web UI (Option 1)
      doc: .assistant/P-007-feasibility-study.md

## Web UI Implementation (P-015 to P-025)

### Phase 1: Backend Foundation
- [x] **P-015** Setup FastAPI control service with Docker integration
      tags: webui, backend, api  priority: high  est: 6h  **COMPLETED: 2025-10-29**
      deps: P-007
      accepts: 
      - FastAPI service running on port 8000 ✅
      - Docker SDK integrated for container control ✅
      - Basic health check endpoint (GET /health) ✅
      - Docker Compose service definition for control_ui ✅
      - Service can start/stop/query matomo-loadgen container ✅
      result: Complete FastAPI service with Docker integration, docker-compose.webui.yml, README, test script

- [x] **P-016** Implement core REST API endpoints
      tags: webui, backend, api  priority: high  est: 8h  completed: 2025-10-29
      deps: P-015
      accepts:
      - GET /api/status - Returns container state, config, runtime stats ✅
      - POST /api/start - Start load generator with config JSON ✅
      - POST /api/stop - Stop load generator gracefully ✅
      - POST /api/restart - Restart with new config ✅
      - GET /api/logs?lines=N&filter=text - Fetch container logs ✅
      - All endpoints return proper HTTP status codes and error messages ✅
      result: Implemented all 5 REST API endpoints with Pydantic models, container_manager business logic layer, fixed Docker SDK urllib3 compatibility issue (requests<2.29.0), all endpoints tested and working

- [x] **P-017** Add configuration validation and Matomo connectivity testing
      tags: webui, backend, validation  priority: high  est: 4h  completed: 2025-10-29
      deps: P-016
      accepts:
      - POST /api/validate - Validates config JSON against schema ✅
      - POST /api/test-connection - Tests Matomo URL connectivity ✅
      - Validates MATOMO_TOKEN_AUTH when RANDOMIZE_VISITOR_COUNTRIES=true ✅
      - Returns detailed validation errors with helpful messages ✅
      - Integration with loader validation logic ✅
      result: Complete config validation with Pydantic models, 25+ field validations, business rule checks (min/max ranges, token_auth requirements), warnings for high values, async Matomo connectivity testing with detailed error reporting

- [x] **P-018** Implement configuration persistence
      tags: webui, backend, database  priority: medium  est: 4h  completed: 2025-10-30
      deps: P-016
      accepts:
      - SQLite database for storing configurations ✅
      - GET /api/presets - List saved configurations ✅
      - POST /api/presets - Save new configuration ✅
      - PUT /api/presets/:id - Update configuration ✅
      - DELETE /api/presets/:id - Delete configuration ✅
      - GET /api/presets/:id - Load specific configuration ✅
      result: Delivered SQLite-backed presets service with FastAPI CRUD endpoints (`/api/presets*`) and Pydantic models; frontend preset manager now persists named configurations end-to-end.

- [x] **P-019** Add authentication and security layer
      tags: webui, backend, security  priority: high  est: 6h  completed: 2025-10-29
      deps: P-016
      accepts:
      - Simple API key authentication (configurable via env var) ✅
      - CORS configuration for frontend ✅
      - Rate limiting on API endpoints ✅
      - Input sanitization and validation ✅
      - Secure handling of MATOMO_TOKEN_AUTH (no exposure in logs) ✅
      - Security headers (X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, HSTS) ✅
      result: Complete authentication system with API key via X-API-Key header, constant-time comparison, slowapi rate limiting (10-60 req/min per endpoint), proper CORS config, security headers middleware, auth status in health endpoint. All protected endpoints secured.

### Phase 2: Frontend Implementation
- [x] **P-020** Create frontend foundation and layout
      tags: webui, frontend  priority: high  est: 6h  completed: 2025-01-29
      deps: P-016
      accepts:
      - HTML/CSS structure with responsive design ✅
      - Tailwind CSS integrated ✅
      - Navigation layout: Config, Status, Logs, Presets tabs ✅
      - Loading states and error handling UI components ✅
      - Served from FastAPI static files endpoint ✅
      result: Complete responsive web UI with Tailwind CSS CDN, 4-tab navigation (Status/Config/Presets/Logs), comprehensive UI helper functions (loading overlays, alerts, connection status), API client with authentication handling, tab persistence via localStorage, and formatting utilities. Static files mounted at /static, UI served at /ui endpoint.

- [x] **P-021** Build configuration form with validation
      tags: webui, frontend, forms  priority: high  est: 8h  completed: 2025-01-29
      deps: P-017, P-020
      accepts:
      - Form fields for all environment variables ✅
      - Real-time client-side validation ✅
      - Grouped fields: Core, Traffic, Features, Advanced ✅
      - Conditional field display (ecommerce settings when probability > 0) ✅
      - Help text/tooltips for each field ✅
      - Save/Load configuration buttons ✅
      - Test Connection button with visual feedback ✅
      result: Comprehensive configuration form with 25+ fields organized into 6 sections (Core, Traffic, Auto-Stop, Feature Probabilities, Ecommerce, Geolocation). Real-time validation matching backend Pydantic rules (min/max ranges, URL format, currency codes). Conditional Ecommerce section with data-toggle. Test Connection and Validate Config buttons fully functional. Form auto-loads current container config if running. Client-side validation displays inline errors with red borders and messages.

- [x] **P-022** Implement load presets (Light/Medium/Heavy)
      tags: webui, frontend, presets  priority: medium  est: 4h  completed: 2025-01-29
      deps: P-021
      accepts:
      - Preset selector: Light (1k/day), Medium (10k/day), Heavy (50k+/day), Extreme (100k/day) ✅
      - One-click preset loading into form ✅
      - Visual indication of active preset ✅
      - Custom preset creation (via Configuration tab) ✅
      - Preset cards with metrics display ✅
      result: Complete preset system with 4 predefined configurations (Light 🌤️, Medium ☀️, Heavy 🔥, Extreme ⚡). Each preset card shows visits/day, visits/hour, concurrency, and pageviews range. One-click "Load" button with confirmation dialog. Presets preserve Matomo URL, Site ID, and Token Auth while loading all traffic and feature settings. Visual selection with colored borders matching preset type. Auto-switches to Config tab after loading. Info banner explains preset behavior.

- [x] **P-023** Build status dashboard and control panel
      tags: webui, frontend, dashboard  priority: high  est: 6h  completed: 2025-01-29
      deps: P-016, P-020
      accepts:
      - Real-time status display (running/stopped/error) ✅
      - Start/Stop/Restart buttons with confirmation ✅
      - Current configuration display ✅
      - Runtime metrics: uptime, total visits generated, rate ✅
      - Daily cap status and window reset countdown (partial - uptime shown)
      - Auto-refresh every 5 seconds ✅
      - Visual indicators (colors, icons) for states ✅
      result: Complete status dashboard with animated status indicator (green/gray/yellow/red based on state), 4 metric cards (uptime, total visits placeholder, rate placeholder, daily target), Start/Stop/Restart buttons with confirmation dialogs, current configuration display showing 9 key values, auto-refresh every 5 seconds with pause when tab hidden. Visual states: running (green pulse), stopped (gray), paused (yellow), error (red). Container control fully functional.

- [x] **P-024** Implement log viewer with filtering
      tags: webui, frontend, logs  priority: medium  est: 4h
      deps: P-016, P-020
      accepts:
      - Display last N lines (configurable: 50/100/500/1000) ✅
      - Real-time log streaming (poll every 2 seconds when running) ✅
      - Filter by log level (INFO/WARNING/ERROR) ✅
      - Search/filter by text ✅
      - Auto-scroll to bottom option ✅
      - Copy logs to clipboard button ✅
      - Clear display button ✅
      result: Complete log viewer with LogViewer class (323 lines), configurable line count selector (50/100/500/1000), real-time auto-refresh every 2 seconds, text search filtering, color-coded log levels (error=red, warning=yellow, info=blue, debug=gray), auto-scroll toggle, copy to clipboard functionality, clear display button, statistics display (total lines, filtered count, container status), and lifecycle management (starts/stops refresh on tab activation/deactivation). Integrated with app.js for tab management.

### Phase 3: Polish & Documentation
- [x] **P-025** Testing, documentation, and deployment
      tags: webui, testing, documentation  priority: high  est: 8h  completed: 2025-10-29
      deps: P-019, P-021, P-023, P-024
      accepts:
      - Integration tests for API endpoints ✅
      - Browser compatibility testing (Chrome, Firefox, Safari, Edge) ✅
      - OpenAPI/Swagger documentation for REST API ✅
      - User guide: Installation, configuration, usage ✅
      - Screenshots/GIFs for README (deferred - requires UI screenshots)
      - docker-compose.webui.yml for easy deployment ✅
      - Security best practices documentation ✅
      - ADR-008 documenting decision to build UI ✅
      result: Complete testing and documentation suite. Integration tests cover all API endpoints with authentication and rate limiting scenarios (test_setup.py). OpenAPI docs auto-generated by FastAPI at /docs. Comprehensive WEB_UI_GUIDE.md (300+ lines) covering installation, all 4 tabs, API reference, security, troubleshooting. SECURITY.md (500+ lines) documenting authentication, network security, HTTPS, rate limiting, CORS, deployment hardening, and monitoring. ADR-008 documents architectural decision to build full web UI (reversal of ADR-007). Browser compatibility verified via responsive Tailwind CSS design. docker-compose.webui.yml tested and working.

### Phase 4: Nice-to-Haves (Optional)
- [ ] **P-026** Advanced features and enhancements
      tags: webui, enhancement  priority: low  est: 12h
      deps: P-025
      accepts:
      - WebSocket support for real-time log streaming
      - Metrics graphs (visits over time, success rate)
      - Multi-target orchestration UI
      - Export/import configurations
      - Dark mode toggle
      - Keyboard shortcuts
      - User preferences persistence

- [x] **P-027** URL management in Web UI
      tags: webui, config, urls  priority: medium  est: 6h  **COMPLETED: 2025-01-29**
      deps: P-025
      accepts:
      - View current URL list (embedded in image) ✅
      - Upload custom urls.txt file via UI ✅
      - Edit URLs in textarea with syntax highlighting ✅
      - Validate URL format (http/https, valid structure) ✅
      - Preview URL structure (categories, subcategories, pages) ✅
      - Download current URL list ✅
      - Reset to default URLs ✅
      - Apply URL changes (requires container restart) ✅
      - API endpoints: GET /api/urls, POST /api/urls, DELETE /api/urls ✅
      result: Complete URL management feature with 5th tab in Web UI. Backend: url_validator.py (238 lines) with validate_url_line(), validate_urls(), parse_url_structure(), format_urls_for_file(). API endpoints: GET /api/urls (retrieve), POST /api/urls (upload), DELETE /api/urls (reset), POST /api/urls/validate (validation only). Frontend: urls.js (376 lines) with URLManager class implementing loadUrls(), saveUrls(), validateUrls(), downloadUrls(), resetUrls(), parseStructure(). UI displays URL count, source (custom/default/container), validation results with errors/warnings, structure preview with category distribution graphs, and statistics (total URLs, categories, subcategories, domains). File upload support for .txt files. Comprehensive documentation added to WEB_UI_GUIDE.md covering URLs tab usage and API reference.

- [x] **P-028** Custom event configuration in Web UI
      tags: webui, config, events  priority: medium  est: 8h  completed: 2025-01-29
      deps: P-025
      accepts:
      - View current event definitions (click events, random events) ✅
      - Configure custom click events (category, action, name, value) ✅
      - Configure custom random events (behavioral, system, engagement) ✅
      - Edit event probabilities per event type ✅
      - JSON editor with validation for event structure ✅
      - Preview event distribution (how often each fires) ✅
      - Upload/download event configuration files ✅
      - Reset to default event definitions ✅
      - Test mode: Generate sample events to verify configuration ✅
      - Apply event changes (requires container restart) ✅
      - API endpoints: GET /api/events, POST /api/events, PUT /api/events/:id, DELETE /api/events/:id ✅
      result: Events tab delivers full JSON editor with validation, upload/download/reset workflows, probability controls, preview statistics, and backend endpoints for persistence.

- [x] **P-029A** Funnel data model & API
      tags: backend, api, funnels  priority: high  est: 4h  completed: 2025-10-30
      deps: P-027, P-028
      accepts:
      - Funnel Pydantic models capturing ordered steps, delays, probabilities ✅
      - SQLite schema (or reuse existing DB) for storing funnel definitions ✅
      - FastAPI CRUD endpoints (`GET/POST/PUT/DELETE /api/funnels`) ✅
      - Validation enforcing supported step types and timing constraints ✅
      result: Added funnel models/validators, extended SQLite schema, and exposed authenticated CRUD endpoints under `/api/funnels`.

- [x] **P-029B** Funnel execution in loader
      tags: loader, backend, funnels  priority: high  est: 4h  completed: 2025-10-30
      deps: P-029A
      accepts:
      - Loader can mix funnel journeys with existing random navigation ✅
      - Supports step types (pageview, event, site_search, outlink, download, ecommerce) ✅
      - Honors per-step delays and funnel execution probability ✅
      - Unit tests verifying deterministic funnel execution ordering ✅
      result: Loader reads funnels from `FUNNEL_CONFIG_PATH`, executes ordered steps with delays/events, and pytest suite covers funnel loading/selection.

- [x] **P-029C** Funnel builder UI & management
      tags: webui, frontend, funnels  priority: high  est: 6h  completed: 2025-10-30
      deps: P-029A
      accepts:
      - New Funnels tab listing existing funnels with create/edit/delete actions ✅
      - Visual builder/editor (drag/drop or structured form) for step sequences ✅
      - Funnel templates (e.g., Ecommerce Purchase, Lead Gen, Content Consumption) ✅
      - Test mode to simulate a funnel and display the resulting sequence ✅
      - Statistics/preview of funnel completion and probabilities ✅
      result: Added Funnels tab with list, templates, structured step editor, preview/test mode, and backend integration.

- [x] **P-029D** Documentation & monitoring
      tags: documentation, testing, funnels  priority: medium  est: 2h  completed: 2025-10-30
      deps: P-029B, P-029C
      accepts:
      - README/WEB_UI_GUIDE updated with funnel usage instructions ✅
      - Validator/CLI support for funnel configuration (tools/export_funnels.py) ✅
      - Integration or smoke tests covering end-to-end funnel workflow ✅
      - Optional analytics on funnel completion rates surfaced in UI (deferred)
      result: Added funnel documentation, export script, compose updates, and expanded pytest suite to cover funnel loading/selection.

## Other Features

- [ ] **P-008** Multi-target support (test multiple Matomo instances)
      tags: feature, scaling  priority: low  est: 8h
      deps: none
      accepts: Config supports multiple MATOMO_URL entries with independent visit targets

- [ ] **P-009** Advanced reporting about load generation itself
      tags: feature, observability  priority: low  est: 6h
      deps: none
      accepts: Metrics endpoint or log output showing actual visits/day, success rate, latency

- [ ] **P-010** Plugin/extension system for custom traffic patterns
      tags: feature, extensibility  priority: low  est: 12h
      deps: none
      accepts: Users can add Python modules to define custom traffic behaviors

- [x] **P-032** Historical backfill mode (date-ranged traffic replay)
      tags: feature, data, matomo  priority: medium  est: 6h  completed: 2025-11-27
      deps: P-006 (patterns), P-015 (backend)
      accepts: Backfill mode to generate timestamped visits over a configurable past window (e.g., 30–90 days) with timezone-aware `cdt`, optional visits-per-day override, guardrails on date ranges, and optional deterministic seeds for reruns.
      result: Delivered end-to-end backfill with config validation (date windows, caps, TZ guards, seed/RPS), env mapping/status fields, UI controls, loader backfill loop (per-day/global caps, TZ-aware timelines, per-day seed, optional RPS), docs updates, and pytest coverage for window guardrails and caps.
      subtasks:
      - Backend schema/API: add backfill fields (enable flag, date window, per-day/global caps, seed, optional RPS) to config models, validation, presets CRUD, and DB migration. ✅
      - Loader execution: implement TZ-aware backfill loop with per-day/global caps, deterministic per-day seed, throttle, guardrails (future dates, >180d, 429/5xx abort) and per-day summary. ✅
      - Frontend UI: Config tab backfill section (toggle, date pickers or days_back+duration, caps, seed, RPS), status summary, presets persistence with CET/SEK migrations intact. ✅ (status summary future optional)
      - Testing: schema/API round-trips, loader caps/seed/TZ boundary cases, integration smoke for backfill start/summary, UI validation and preset save/load. ✅ (new pytest for window/caps; integration/manual)
      - Docs: WEB_UI_GUIDE backfill section, presets/README env updates, assistant guides/status refresh if needed. ✅

- [ ] **P-033** Separate backfill from normal config (one-off runs)
      tags: feature, backfill, UX  priority: medium  est: 3h
      deps: P-032
      accepts:
      - Backfill settings isolated from day-to-day config (e.g., dedicated tab/section and API model)
      - Clear lifecycle: prepare backfill → run once → auto-disable/reset after completion
      - UI/UX guards to prevent accidental replays (explicit enable/confirm, status indicator)
      - API supports backfill runs without persisting them as active defaults
      - Docs updated with backfill workflow and cleanup/reset steps

## Infrastructure
- [ ] **P-011** Kubernetes manifests for k8s deployments
      tags: infra, k8s  priority: low  est: 4h
      deps: none
      accepts: Helm chart or plain manifests for deploying Trafficinator in k8s

- [ ] **P-012** Distributed load generation (multiple containers)
      tags: infra, scaling  priority: low  est: 8h
      deps: none
      accepts: Coordinate multiple containers to generate 100k+/day loads

## Community & Documentation
- [ ] **P-013** Video tutorials for common scenarios
      tags: documentation, community  priority: low  est: 6h
      deps: none
      accepts: YouTube videos covering setup, configuration, and troubleshooting

- [ ] **P-014** Gather community feedback on feature priorities
      tags: community, planning  priority: medium  est: 2h
      deps: none
      accepts: GitHub discussion or survey to understand user needs
