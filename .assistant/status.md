# Status

**Last Updated:** 2025-01-29 (Phase 2 Frontend Implementation Started)

---

## Focus
🎨 **Web UI Phase 2: Frontend Implementation** - Building responsive web interface with configuration forms, status dashboard, and log viewer.

**Current Priority:** Phase 2 - Frontend Features (P-020 ✅, P-021, P-023, P-024)

---

## Now / Next / Later
See [plan.md](plan.md) for detailed roadmap.

**Now:** Phase 2 frontend features - P-021 (config form), P-023 (status dashboard), P-024 (log viewer), P-022 (presets)  
**Next:** Phase 3 polish - P-025 (UI enhancements), P-026 (integration testing), documentation updates  
**Later:** Nice-to-have features, advanced UI capabilities, community features

---

## Risks

### Technical
- **Web UI Complexity:** Adding web service increases attack surface and maintenance burden
- **State Synchronization:** Keeping UI state in sync with container state
- **Browser Compatibility:** Must test across multiple browsers
- **Security:** Auth, CORS, input validation, API abuse prevention
- **Token-bucket rate limiting:** May not handle burst scenarios optimally (existing)
- **Single-container scaling:** Limited to ~50k visits/day without distributed mode (existing)

### Product
- **Feature Creep:** UI may attract more feature requests, expanding scope
- **Maintenance Burden:** Single maintainer now responsible for backend + frontend + generator
- **User Expectations:** UI users may expect more polish and features
- **Documentation Load:** Need comprehensive UI docs in addition to existing docs

### Operational
- **Deployment Complexity:** Two services (generator + control UI) vs. one
- **Testing Complexity:** Integration testing between UI and generator
- **Support Load:** More questions about UI configuration, browser issues
- **Version Compatibility:** UI and generator versions must stay in sync

---

## Artifacts

### Core
- `matomo-load-baked/loader.py` (929 lines) — Main load generator
- `docker-compose.yml` — Development/local configuration
- `docker-compose.prod.yml` — Production deployment with Watchtower
- `docker-compose.webui.yml` — Two-service deployment (generator + control UI)
- `config/urls.txt` — 2,000 pre-built URLs (embedded in image)

### Control UI (NEW)
- `control-ui/app.py` (413 lines) — FastAPI application with REST API
- `control-ui/static/index.html` (132 lines) — Responsive web interface
- `control-ui/static/js/api.js` (134 lines) — API client with authentication
- `control-ui/static/js/ui.js` (180 lines) — UI helper functions
- `control-ui/static/js/app.js` (101 lines) — Application controller
- `control-ui/docker_client.py` — Docker SDK wrapper
- `control-ui/container_manager.py` — Container control logic
- `control-ui/config_validator.py` — Pydantic validation & Matomo connectivity
- `control-ui/auth.py` — API key authentication
- `control-ui/models.py` — Request/response models


### Documentation
- `README.md` — Primary user documentation
- `DEPLOYMENT.md` — Remote deployment guide
- `CLAUDE.md` — Development/AI assistant context (needs updates)
- `ecommerce_design.md` — Ecommerce feature design notes

### Test & Debug
- `matomo-load-baked/tests/` — Unit tests for action ordering
- `debug_loader.py` — Request debugging script
- `check_ranges.py`, `test_*.py` — Validation scripts

### Assistant Memory
- `.codex/memory.md` — Historical decisions and context
- `.codex/webui-parked.md` — Postponed web UI features
- `.assistant/` — New workflow directory (this migration)

---

## Changelog

### 2025-01-29 — P-020 Complete: Frontend Foundation
- **Phase 2 Started:** Frontend implementation underway
- Created responsive web UI with Tailwind CSS (CDN-based)
- Built 4-tab navigation: Status, Config, Presets, Logs
- Implemented comprehensive UI helpers (loading, alerts, formatting)
- Created API client with authentication and error handling
- Added application controller with auto-refresh and lifecycle management
- Integrated static file serving in FastAPI
- Web UI accessible at http://localhost:8000/ui
- **Deliverables:** 4 new files (~550 lines frontend code), app.py updates
- **Next:** P-021 (configuration form) or P-023 (status dashboard) - can parallelize

### 2025-10-29 — P-019 Complete: Authentication & Security
- API key authentication via X-API-Key header
- Rate limiting with slowapi (10-60 req/min per endpoint)
- CORS middleware with configurable origins
- Security headers (X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, HSTS)
- Constant-time API key comparison (timing attack prevention)
- Fixed Docker SDK compatibility (urllib3<2, requests<2.29.0, docker 6.1.3)

### 2025-10-29 — P-017 Complete: Config Validation
- Comprehensive Pydantic validation for 25+ configuration fields
- Business rule validation (min <= max, percentages sum to 100%)
- Async Matomo connectivity testing
- Warning system for high-value configurations
- Validation endpoint with detailed error messages

### 2025-10-29 — P-016 Complete: Core REST API
- 7 API endpoints implemented (status, start, stop, restart, logs, validate, test-connection)
- Request/response models with Pydantic
- Container manager layer with proper error handling
- Docker SDK integration with unix socket support
- Rate limiting applied to all endpoints

### 2025-10-29 — P-015 Complete: FastAPI Service Setup
- FastAPI application scaffolded
- Docker integration with compose file
- Requirements and environment configuration
- Test scripts and documentation
- Health check and root endpoints

### 2025-10-29 — DECISION: Build Full Web UI (Reversal of ADR-007)
- **Major decision:** Proceeding with Full Web UI (Option 1 from P-007 feasibility study)
- Created 12 new backlog items (P-015 to P-026) for implementation
- Organized into 4 phases: Backend Foundation, Frontend Implementation, Polish & Documentation, Nice-to-Haves
- Total estimated effort: 56h core + 12h optional enhancements
- Risks identified and documented (security, complexity, maintenance)
- Plan updated to prioritize Web UI development
- **Rationale:** Despite feasibility study recommendation, user decided UI value outweighs maintenance cost
- **Next:** Start with P-015 (FastAPI service setup)

### 2025-10-29 — P-007 Feasibility Study Complete
- Evaluated Control UI/API feasibility (4 options analyzed)
- **Recommendation:** Maintain status quo with improvements (validation + presets)
- Decision: Do not build UI unless strong community demand emerges (5+ issues, 100+ stars)
- Triggers identified for reconsidering: community growth, external maintainer, user surveys
- Next: Focus on P-004 (validation) and P-005 (presets) instead

### 2025-10-29 — Migration to `.assistant/` Workflow
- Populated `.assistant/canvas/` with vision, goals, stakeholders, questions, ideas, notes
- Created structured backlog with 14 P-IDs (P-001 through P-014)
- Organized plan.md with Now/Next/Later priorities
- Documented project history from commits and memory
- Generated fresh status.md with risks and artifacts
- Next: Create ADR stubs for key architectural decisions

### 2025-09-10 — Web UI Postponed
- Removed `control_ui` scaffold
- Parked web UI tasks in `.codex/webui-parked.md`
- Backlog pruned to generator-focused features

### 2025-09-07 — Behavior & Daily Cap
- Event ordering guarantees (never first action)
- Per-24h `MAX_TOTAL_VISITS` with pause/resume
- Run indefinitely by default

### 2025-09-01 — Major Features
- Ecommerce orders (50+ products, realistic patterns)
- Timezone configuration
- Traffic source diversification
- Global geolocation with IP ranges
- Production deployment pipeline

### 2025-08-31 — Custom Events
- Click events (25%) and random events (12%)
- Rich metadata with Matomo compliance

### Earlier
- Site search simulation
- Outlinks and downloads tracking
- Extended visit durations (1-8 min)
- Core load generation with token-bucket algorithm

---

## Open Questions (from canvas/questions.md)

### High Priority
- **Q1:** Should we add a control API? (Currently parked)
- **Q4:** Right balance between realism and configurability?
- **Q10:** What documentation is missing for first-time users?

### Medium Priority
- **Q2:** Is token-bucket optimal for all scenarios?
- **Q5:** Need more sophisticated user journey modeling?
- **Q8:** Is Watchtower the right auto-update strategy?

### Low Priority
- **Q3:** Distributed load generation support?
- **Q6:** Traffic replay from actual logs?
- **Q7:** Kubernetes manifest demand?
- **Q9:** SaaS-style hosted offering?
- **Q11:** Video tutorial investment worth it?

See [canvas/questions.md](canvas/questions.md) for full context.
