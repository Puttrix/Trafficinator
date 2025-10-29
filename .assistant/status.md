# Status

**Last Updated:** 2025-10-29 (Decision to build Web UI)

---

## Focus
🚀 **Web UI Development** - Building FastAPI control service and web interface for easier configuration and monitoring.

**Current Priority:** Phase 1 - Backend Foundation (P-015, P-016, P-017)

---

## Now / Next / Later
See [plan.md](plan.md) for detailed roadmap.

**Now:** Backend foundation (P-015, P-016, P-017), validation utilities (P-004), presets (P-005)  
**Next:** Backend completion (P-018, P-019), frontend core (P-020, P-021, P-023, P-024), integration (P-022, P-025)  
**Later:** UI enhancements (P-026), documentation updates, advanced generator features

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
- `config/urls.txt` — 2,000 pre-built URLs (embedded in image)

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
