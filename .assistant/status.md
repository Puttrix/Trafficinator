# Status

**Last Updated:** 2025-11-26 (CET/SEK defaults + Extreme preset + funnel suite)

---

## Focus
- Prepare multi-target support (P-008) design while monitoring CET/SEK default migrations in UI/presets.

---

## Now / Next / Later
- **Now:** Shape P-008 (multi-target config/API/loader expectations) and verify default migrations didn’t regress saved presets.
- **Next:** Plan P-032 historical backfill mode (date-ranged replay, guardrails, timezone handling) and deepen user journey realism (P-006).
- **Later:** P-026 enhancements (websocket logs, graphs, dark mode) plus P-009/P-010 observability/extensibility once core flows stabilize.

---

## Risks
- **Config drift:** Multi-target schemas could desync between backend models, DB, and UI forms.
- **Back-compat:** Legacy presets with UTC/USD values may surface unless migrations stay enforced end-to-end.
- **Testing gap:** Limited automated coverage for new funnels/URL/event editors; multi-target/backfill changes need regression tests.
- **Data safety:** Historical replay (P-032) needs strict date guards to avoid over-posting visits.

---

## Artifacts
- `control-ui/app.py`, `db.py`, `models.py` — FastAPI + SQLite core.
- `control-ui/static/js/{app,config,presets,urls,funnels}.js` — UI controllers for config, presets, URLs, events, funnels.
- `control-ui/static/index.html` — Web UI shell (Tailwind CDN).
- `matomo-load-baked/loader.py` — Loader with funnels and CET/SEK defaults.
- `tools/validate_config.py` — CLI validator and Matomo connectivity probe.
- `presets/.env.{light,medium,heavy,extreme}` — Prebuilt presets (CET/SEK defaults).
- `WEB_UI_GUIDE.md`, `.assistant/ai_guidance.md` — User + assistant guides.

---

## Recent Progress
- Defaulted timezone to CET and ecommerce currency to SEK across loader, UI defaults/placeholders, and preset definitions.
- Added Extreme preset file to match UI preset and documented it.
- Applied UI migrations so legacy UTC/USD presets convert to CET/SEK on load.
- Delivered funnels: backend models + CRUD (P-029A), loader execution with tests (P-029B), UI builder/templates (P-029C), and docs/export/tests (P-029D).
- Completed P-015–P-025 foundation: API, validation, security, UI tabs (Config/Status/Logs/Presets/URLs/Events), and documentation/testing baseline.

---

## Open Questions
- How should multi-target configs be structured (per-target auth, weights, caps) and reflected in API/UI?
- Should CET/SEK migrations also rewrite persisted presets on save to avoid mixed defaults?
- For backfill (P-032), what date limits and rate controls prevent runaway load in production Matomo?
