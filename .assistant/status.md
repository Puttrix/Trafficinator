# Status

**Last Updated:** 2025-10-29 (Migration to `.assistant/` workflow)

---

## Focus
Documentation alignment and test coverage improvements. Project in maintenance mode with occasional enhancements.

---

## Now / Next / Later
See [plan.md](plan.md) for detailed roadmap.

**Now:** Documentation updates (P-001, P-002), test coverage enhancement (P-003)  
**Next:** Validation utilities (P-004), load presets (P-005), user journeys (P-006)  
**Later:** Advanced features (control UI, multi-target, k8s, plugins)

---

## Risks

### Technical
- **Token-bucket rate limiting:** May not handle burst scenarios optimally
- **Single-container scaling:** Limited to ~50k visits/day without distributed mode
- **Geolocation dependency:** Requires `MATOMO_TOKEN_AUTH` which may expire or be revoked

### Product
- **Feature creep:** Balancing realism vs. configurability complexity
- **Maintenance burden:** Single maintainer with limited capacity
- **Community engagement:** Unclear user needs without active feedback channel

### Operational
- **Documentation drift:** CLAUDE.md contains outdated references (P-001, P-002)
- **Test coverage gaps:** Complex behaviors (events, ecommerce, daily cap) under-tested
- **Deployment complexity:** Multiple compose files may confuse new users

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
