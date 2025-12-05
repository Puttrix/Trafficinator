# Status

**Last Updated:** 2025-12-05 (P-032 complete, PR pending)

---

## Focus
- Merge backfill feature (P-032) from `develop→main`; then shape multi-target support (P-008).

---

## Now / Next / Later
- **Now:** Create PR for P-032 backfill release; merge to main; tag v0.3.0.
- **Next:** Design P-008 (multi-target config/API/loader) and deepen user journey realism (P-006).
- **Later:** P-026 enhancements (websocket logs, graphs, dark mode) plus P-009/P-010 observability/extensibility.

---

## Risks
- **Config drift:** Multi-target schemas could desync between backend models, DB, and UI forms.
- **Back-compat:** Legacy presets with UTC/USD values may surface unless migrations stay enforced end-to-end.
- **Testing gap:** Limited automated coverage for new funnels/URL/event editors; backfill integration tested via unit tests.

---

## Artifacts
- `control-ui/app.py`, `db.py`, `models.py`, `config_validator.py`, `container_manager.py` — FastAPI + SQLite core + backfill validation.
- `control-ui/static/js/{app,config,presets,urls,funnels,status}.js` — UI controllers including backfill config/status.
- `control-ui/static/index.html` — Web UI shell (Tailwind CDN) with Backfill section.
- `matomo-load-baked/loader.py` — Loader with funnels, backfill mode, CET/SEK defaults.
- `matomo-load-baked/tests/test_backfill.py` — pytest coverage for backfill windows/caps.
- `tools/validate_config.py` — CLI validator and Matomo connectivity probe.
- `presets/.env.{light,medium,heavy,extreme}` — Prebuilt presets (CET/SEK defaults).
- `WEB_UI_GUIDE.md`, `presets/README.md` — Backfill usage documentation.

---

## Recent Progress
- **P-032 Complete:** Historical backfill mode delivered end-to-end:
  - Config validation (date windows ≤180d, no future dates, caps, TZ guards, seed/RPS)
  - Env mapping and status model fields
  - UI: Config tab Backfill section, Status tab Backfill panel
  - Loader: TZ-aware backfill loop, per-day/global caps, deterministic seeds, optional RPS
  - Tests: pytest coverage for window guardrails and caps (4 tests)
  - Docs: WEB_UI_GUIDE and presets/README updated
- `develop` branch ahead of `main` by 5 commits (backfill feature)
- No open PRs; no uncommitted changes

---

## Pending Actions
- [x] Create PR `develop→main` for P-032 release — **PR #11**: https://github.com/Puttrix/Trafficinator/pull/11
- [ ] Merge and tag v0.3.0
- [ ] Update backlog with next focus (P-008/P-006)

---

## Open Questions
- How should multi-target configs be structured (per-target auth, weights, caps) and reflected in API/UI?
- Should CET/SEK migrations also rewrite persisted presets on save to avoid mixed defaults?
