# Status

**Last Updated:** 2025-10-30 (P-018 Configuration Persistence Complete)

---

## Focus
- Capture follow-up QA for the new presets API and tee up Phase 3 polish (P-025 documentation/testing, P-026 enhancements).

---

## Now / Next / Later
- **Now:** Verify presets persistence end-to-end when runtime is available and note any integration gaps for QA.
- **Next:** Phase 3 polish — P-025 testing + documentation refresh, P-026 enhancement triage.
- **Later:** Phase 4 nice-to-haves (advanced features, metrics, websockets) once polish is stable.

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

---

## Recent Progress
- Completed P-015 through P-017 (FastAPI service, REST endpoints, validation + Matomo connectivity).
- Security baseline (P-019) landed: API key auth, CORS, rate limiting, headers.
- Frontend skeleton (P-020+) committed: responsive layout, config form, status dashboard, presets, log viewer.

---

## Open Questions
- Do we need optimistic locking/version stamps for saved configs?
- Should presets live in the same table as ad-hoc configs or stay file-based?
- How are secrets (tokens) persisted—store hashed, encrypted, or prompt on load?
