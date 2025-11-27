# Status

**Last Updated:** 2025-11-27 (Backfill mode delivered)

---

## Focus
- Prepare multi-target support (P-008) design while monitoring CET/SEK default migrations in UI/presets; backfill (P-032) shipped with docs/tests.

---

## Now / Next / Later
- **Now:** Shape P-008 (multi-target config/API/loader expectations) and verify default migrations didn’t regress saved presets.
- **Next:** Deepen user journey realism (P-006) and harden backfill with optional status/progress surfaces if needed.
- **Later:** P-026 enhancements (websocket logs, graphs, dark mode) plus P-009/P-010 observability/extensibility once core flows stabilize.

---

## Risks
- **Config drift:** Multi-target schemas could desync between backend models, DB, and UI forms.
- **Back-compat:** Legacy presets with UTC/USD values may surface unless migrations stay enforced end-to-end.
- **Testing gap:** Limited automated coverage for new funnels/URL/event editors; backfill integration still light beyond unit tests.
- **Data safety:** Backfill must retain guards against over-posting; future status/progress surfaces should avoid leaking secrets.

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
- Delivered historical backfill mode (P-032): config validation (date windows, caps, TZ guards, seed/RPS), env mapping, UI controls, loader loop (per-day/global caps, TZ-aware timelines, per-day seed, optional RPS), docs, and pytest coverage for window/cap guardrails.
- Defaulted timezone to CET and ecommerce currency to SEK across loader, UI defaults/placeholders, and preset definitions.
- Added Extreme preset file to match UI preset and documented it.
- Applied UI migrations so legacy UTC/USD presets convert to CET/SEK on load.
- Completed P-015–P-025 foundation: API, validation, security, UI tabs (Config/Status/Logs/Presets/URLs/Events), and documentation/testing baseline.

---

## Open Questions
- How should multi-target configs be structured (per-target auth, weights, caps) and reflected in API/UI?
- Should CET/SEK migrations also rewrite persisted presets on save to avoid mixed defaults?
- Do we want Status tab surfacing backfill progress/summary or keep it console-only?
