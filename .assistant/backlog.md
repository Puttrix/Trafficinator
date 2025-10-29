# Backlog

## Documentation & Alignment
- [ ] **P-001** Update CLAUDE.md to reference correct docker-compose files
      tags: documentation, maintenance  priority: medium  est: 1h
      deps: none
      accepts: CLAUDE.md references docker-compose.yml and docker-compose.prod.yml instead of docker-compose.loadgen.yml; notes URLs are embedded in image

- [ ] **P-002** Update CLAUDE.md to reflect embedded URLs vs config/urls.txt
      tags: documentation, maintenance  priority: medium  est: 0.5h
      deps: P-001
      accepts: Documentation clearly states URLs are built into Docker image

## Testing & Quality
- [ ] **P-003** Enhance test coverage for complex behaviors
      tags: testing, quality  priority: high  est: 4h
      deps: none
      accepts: Tests cover events, ecommerce, daily cap, and action ordering guarantees

- [ ] **P-004** Add validation utilities for configuration
      tags: testing, devx  priority: medium  est: 3h
      deps: none
      accepts: Script validates env vars and tests Matomo connectivity before load test

## Features - Short Term
- [ ] **P-005** Create load preset configurations (Light/Medium/Heavy)
      tags: feature, usability  priority: low  est: 2h
      deps: none
      accepts: Example compose files or env templates for Light (1k/day), Medium (10k/day), Heavy (50k+/day)

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

- [ ] **P-018** Implement configuration persistence
      tags: webui, backend, database  priority: medium  est: 4h
      deps: P-016
      accepts:
      - SQLite database for storing configurations
      - GET /api/configs - List saved configurations
      - POST /api/configs - Save new configuration
      - PUT /api/configs/:id - Update configuration
      - DELETE /api/configs/:id - Delete configuration
      - GET /api/configs/:id - Load specific configuration

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

- [ ] **P-021** Build configuration form with validation
      tags: webui, frontend, forms  priority: high  est: 8h
      deps: P-017, P-020
      accepts:
      - Form fields for all environment variables
      - Real-time client-side validation
      - Grouped fields: Core, Traffic, Features, Advanced
      - Conditional field display (e.g., show token_auth when country randomization enabled)
      - Help text/tooltips for each field
      - Save/Load configuration buttons
      - Test Connection button with visual feedback

- [ ] **P-022** Implement load presets (Light/Medium/Heavy)
      tags: webui, frontend, presets  priority: medium  est: 4h
      deps: P-021
      accepts:
      - Preset selector dropdown: Light (1k/day), Medium (10k/day), Heavy (50k+/day)
      - One-click preset loading into form
      - Visual indication of active preset
      - Custom preset creation and saving
      - Integrates with P-005 preset definitions

- [ ] **P-023** Build status dashboard and control panel
      tags: webui, frontend, dashboard  priority: high  est: 6h
      deps: P-016, P-020
      accepts:
      - Real-time status display (running/stopped/error)
      - Start/Stop/Restart buttons with confirmation
      - Current configuration display
      - Runtime metrics: uptime, total visits generated, rate
      - Daily cap status and window reset countdown
      - Auto-refresh every 5 seconds
      - Visual indicators (colors, icons) for states

- [ ] **P-024** Implement log viewer with filtering
      tags: webui, frontend, logs  priority: medium  est: 4h
      deps: P-016, P-020
      accepts:
      - Display last N lines (configurable: 50/100/500/1000)
      - Real-time log streaming (poll every 2 seconds when running)
      - Filter by log level (INFO/WARNING/ERROR)
      - Search/filter by text
      - Auto-scroll to bottom option
      - Copy logs to clipboard button
      - Clear display button

### Phase 3: Polish & Documentation
- [ ] **P-025** Testing, documentation, and deployment
      tags: webui, testing, documentation  priority: high  est: 8h
      deps: P-019, P-021, P-023, P-024
      accepts:
      - Integration tests for API endpoints
      - Browser compatibility testing (Chrome, Firefox, Safari, Edge)
      - OpenAPI/Swagger documentation for REST API
      - User guide: Installation, configuration, usage
      - Screenshots/GIFs for README
      - docker-compose.webui.yml for easy deployment
      - Security best practices documentation
      - ADR-008 documenting decision to build UI

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
