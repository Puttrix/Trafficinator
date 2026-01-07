# Status

**Last Updated:** 2026-01-07

---

## Focus
- Deliver P-033 one-off backfill runs and align UX/docs with the new flow.

---

## Now / Next / Later
- **Now:** P-033 separate backfill runs (API/UX guardrails, run-once lifecycle, docs).
- **Next:** P-006 journey realism; P-008 multi-target config/API/loader design.
- **Later:** P-009 reporting, P-010 extensions, P-011/12 infra scaling.

---

## Risks
- **UX safety:** One-off backfill must avoid accidental replays or persistent config drift.
- **Config drift:** Multi-target schemas could desync across backend models, DB, and UI forms.
- **Testing gap:** Limited automated coverage for backfill run flows and multi-target edge cases.

---

## Artifacts
- `control-ui/app.py`, `control-ui/models.py`, `control-ui/container_manager.py` — FastAPI control service and config/backfill support.
- `control-ui/static/js/{app,config,presets,funnels,status}.js` — UI controllers and config UX.
- `matomo-load-baked/loader.py` — Traffic generator with backfill and funnel execution.
- `matomo-load-baked/tests/test_backfill.py` — pytest coverage for backfill windows/caps.
- `tools/validate_config.py`, `tools/export_funnels.py` — CLI helpers for validation/funnel export.
- `presets/.env.{light,medium,heavy,extreme}` — Preset env templates.
- `WEB_UI_GUIDE.md`, `presets/README.md` — User-facing docs.

---

## Recent Progress
- Completed P-032 historical backfill end-to-end (validation, UI, loader, tests, docs).
- Defaulted timezone to CET and ecommerce currency to SEK across UI/presets/loader with legacy migration.
- Added funnels CRUD, UI editor, and export workflow with shared volume sync.

---

## Pending Actions
- [ ] Implement P-033 one-off backfill run lifecycle and guardrails.
- [ ] Update backlog for P-006/P-008 sequencing once P-033 scope is locked.

---

## Open Questions
- What is the safest UX for a run-once backfill (dedicated tab vs modal run)?
- Should P-033 store run history separately from persistent presets?
