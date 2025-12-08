# Status

**Last Updated:** 2025-12-08 (P-032 merged to main; tag pending)

---

## Focus
- Finalize P-032 backfill release (tag v0.3.0, release notes) and prepare multi-target design (P-008) plus richer journeys (P-006).

---

## Now / Next / Later
- **Now:** Tag v0.3.0 on main and note release highlights for P-032.
- **Next:** Shape P-008 multi-target config/API/loader design and coordinate with P-006 journey realism.
- **Later:** P-026 enhancements (websocket logs, graphs, dark mode) and observability/extensibility (P-009/P-010).

---

## Risks
- **Config drift:** Multi-target schemas could desync across backend models, DB, and UI forms.
- **Back-compat:** Legacy presets with UTC/USD defaults may reappear unless migrations run end-to-end.
- **Testing gap:** Limited automated coverage for new funnels/URL/event editors; backfill integration relies on targeted unit tests.

---

## Artifacts
- `control-ui/app.py`, `db.py`, `models.py`, `config_validator.py`, `container_manager.py` — FastAPI core with backfill validation.
- `control-ui/static/js/{app,config,presets,urls,funnels,status}.js` — UI controllers including backfill config/status.
- `control-ui/static/index.html` — Web UI shell (Tailwind CDN) with Backfill section.
- `matomo-load-baked/loader.py` — Loader with funnels, backfill mode, CET/SEK defaults.
- `matomo-load-baked/tests/test_backfill.py` — pytest coverage for backfill windows/caps.
- `tools/validate_config.py` — CLI validator and Matomo connectivity probe.
- `presets/.env.{light,medium,heavy,extreme}` — Prebuilt presets (CET/SEK defaults).
- `WEB_UI_GUIDE.md`, `presets/README.md` — Backfill usage documentation.

---

## Recent Progress
- **P-033 kickoff:** Added one-off backfill flow backend — new `/api/backfill/run` endpoint launches ephemeral backfill container (no main config mutation); loader supports `BACKFILL_RUN_ONCE` and idles after run to avoid restart loops.
- **Startup Control:** Added `AUTO_START`/`START_SIGNAL_FILE` gating so webui deployments keep the generator idle until Start is triggered; Control UI start/restart now writes the start signal; loader waits for the flag; tests added.
- **P-032 Bug Fix:** Added `format_cdt()` to send Matomo `cdt` in UTC; tests confirm CET→UTC conversion.
- **P-032 Complete:** End-to-end backfill (validation, UI, loader caps/seed/RPS, docs, pytest coverage); merged `develop`→`main` via PR #11.
- Verified `matomo-load-baked/tests/test_backfill.py` (5 passed).

---

## Pending Actions
- [x] Create PR `develop→main` for P-032 release — **PR #11**: https://github.com/Puttrix/Trafficinator/pull/11
- [x] Merge PR #11 to main
- [ ] Tag v0.3.0 and update release notes
- [ ] Update backlog for next focus (P-008/P-006)

---

## Open Questions
- How should multi-target configs be structured (per-target auth, weights, caps) and reflected in API/UI?
- Should CET/SEK migrations also rewrite persisted presets on save to avoid mixed defaults?
