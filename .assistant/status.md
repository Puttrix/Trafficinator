# Status

**Last Updated:** 2025-11-26 (P-008 Multi-Target Support - In Progress)

---

## Focus
- Finalize multi-target support end-to-end (loader + Control UI) and stabilize config schema (P-008).
- Prep docs/release notes so presets and single-target configs remain backward compatible.

---

## Now / Next / Later
- **Now:** Validate multi-target flows across loader/UI, finish metrics display, and tighten validation/error handling.
- **Next:** Document P-008 (user guide + API notes), run regression + multi-target tests, and ready a release candidate.
- **Later:** Phase 3 polish (P-025/P-026) and advanced features once P-008 ships.

---

## Risks
- **Schema drift:** Single vs. multi-target schema must stay in sync between loader env parsing and Control UI forms.
- **Migration:** Legacy `.env` users need smooth defaults without forcing multi-target fields.
- **Partial failures:** Need consistent behavior/reporting when some targets degrade or fail.
- **Coverage:** Limited automated tests for UI-driven config flows; regressions possible during refactors.

---

## Artifacts
- `control-ui/app.py`, `control-ui/db.py`, `control-ui/models.py` — FastAPI, persistence, and shared schema.
- `control-ui/static/js/app.js`, `config.js`, `multi_target.js`, `status.js`, `control-ui/static/index.html` — Frontend controller, config form, multi-target manager, and metrics UI.
- `matomo-load-baked/loader.py`, `matomo-load-baked/target_router.py` — Loader with single/multi-target routing and distribution strategies.
- `matomo-load-baked/tests/test_multi_target.py` — Coverage for TargetRouter, strategies, env parsing, and edge cases.
- `docker-compose.webui.yml`, `presets/.env.*` — Compose stack and preset configs.
- `.assistant/adr/ADR-009-multi-target-architecture.md`, `.assistant/ai_guidance.md`
- `tools/validate_config.py`
- [GitHub Issue #8](https://github.com/Puttrix/Trafficinator/issues/8) — P-008 spec.

---

## Recent Progress
- Shipped multi-target routing for loader with round-robin/weighted/random strategies and per-target metrics.
- Added comprehensive multi-target tests (env parsing, distribution logic, health/metrics) alongside existing suite.
- Implemented Control UI multi-target manager (add/remove/test targets, mode toggle, distribution strategy, weight inputs).
- Updated Status UI to show per-target metrics and health badges; Config form persists multi-target fields.
- Captured architecture decisions in ADR-009 and linked GitHub Issue #8 for scope/acceptance.

---

## Open Questions
- Do we need optimistic locking/version stamps for saved configs?
- Should presets live in the same table as ad-hoc configs or stay file-based?
- How are secrets (tokens) persisted—store hashed, encrypted, or prompt on load?
- **P-008 Multi-target:** Should target configs be a separate table or embedded JSON in presets table?
- **P-008 Multi-target:** How to handle partial failures (some targets succeed, others fail)?
- **P-008 Multi-target:** Should we support per-target feature flags (e.g., ecommerce on some, not others)?
