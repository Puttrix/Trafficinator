# Status

**Last Updated:** 2025-11-01 (P-008 Multi-Target Support - In Progress)

---

## Focus
- Implement multi-target support for distributing load across multiple Matomo instances (P-008).
- Research completed; backend design phase underway.

---

## Now / Next / Later
- **Now:** P-008 Multi-target support — Design data models, implement async distribution logic, update UI.
- **Next:** Testing and documentation for P-008; Phase 3 polish (P-025, P-026) if needed.
- **Later:** Phase 4 nice-to-haves (advanced features, metrics, websockets) once core features stable.

---

## Risks
- **Data integrity:** Need consistent schema between backend models and frontend form payloads.
- **Migration:** Must handle legacy `.env`-only setups without breaking existing deployments.
- **Concurrency:** Simultaneous edits from multiple sessions could cause stale writes without extra safeguards.
- **Testing gap:** Limited automated coverage for DB-backed flows; regression risk during refactors.

---

## Artifacts
- `control-ui/app.py` — FastAPI entrypoint with routing.
- `control-ui/db.py` — SQLite session helpers (expanding for P-018).
- `control-ui/models.py` — Pydantic models shared across API.
- `control-ui/static/js/app.js` — Frontend controller orchestrating API calls.
- `docker-compose.webui.yml` — Compose stack for control UI + generator.
- `.assistant/ai_guidance.md` — Current AI-assistant quickstart (replaces legacy CLAUDE.md).
- `tools/validate_config.py` — CLI validator for environment variables and Matomo connectivity.
- `presets/.env.*` — Ready-to-use Light/Medium/Heavy environment presets for Docker Compose.
- [GitHub Issue #8](https://github.com/Puttrix/Trafficinator/issues/8) — P-008 multi-target support specification.

---

## Recent Progress
- Completed P-015 through P-017 (FastAPI service, REST endpoints, validation + Matomo connectivity).
- Security baseline (P-019) landed: API key auth, CORS, rate limiting, headers.
- Frontend skeleton (P-020+) committed: responsive layout, config form, status dashboard, presets, log viewer.
- Added pytest coverage for ecommerce/events plus CLI validation utility (P-003/P-004).
- Published Docker Compose presets for Light/Medium/Heavy workloads (P-005).
- Delivered funnel data model and CRUD API groundwork (P-029A) ahead of loader/UI implementation.
- Loader now executes funnel journeys with probability/priority rules and tests (P-029B).
- Built Funnels UI tab with templates, editor, and preview to manage journeys (P-029C).
- Documented funnel workflow, added export CLI, and updated compose sharing (P-029D).

---

## Open Questions
- Do we need optimistic locking/version stamps for saved configs?
- Should presets live in the same table as ad-hoc configs or stay file-based?
- How are secrets (tokens) persisted—store hashed, encrypted, or prompt on load?
- **P-008 Multi-target:** Should target configs be a separate table or embedded JSON in presets table?
- **P-008 Multi-target:** How to handle partial failures (some targets succeed, others fail)?
- **P-008 Multi-target:** Should we support per-target feature flags (e.g., ecommerce on some, not others)?
