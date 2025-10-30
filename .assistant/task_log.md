# Task Log

## 2025-10-30
- tool: shell (`bash -lc "sed -n '1,200p' control-ui/app.py"`; `bash -lc "sed -n '400,520p' control-ui/static/js/presets.js"`).
- result: Reviewed backend FastAPI routes and frontend preset manager; confirmed `/api/presets` CRUD endpoints are absent even though the UI calls them, explaining why configuration persistence (P-018) fails.
- artifacts: none

- tool: apply_patch (control-ui/app.py, control-ui/models.py)
- result: Added FastAPI `/api/presets` CRUD endpoints backed by SQLite, plus Pydantic request/response models so the UI can list, create, update, and delete saved configurations with proper auth, rate limiting, and error handling.
- artifacts: none

- tool: shell (`bash -lc "python3 - <<'PY' ..."` smoke test)
- result: Exercised the SQLite helper against a temp database; create/list/get/update/delete all behaved as expected, confirming the persistence layer supporting the new endpoints works without a running FastAPI server.
- artifacts: none

- tool: shell (`bash -lc "source ~/.zshrc ... && python3 -m pip install --user -r control-ui/requirements.txt"`)
- result: Installed FastAPI/uvicorn, docker SDK, pydantic, and related dependencies so the Control UI service (and P-018 presets API) can run locally for verification; binaries landed under `~/Library/Python/3.9/bin` (add to PATH if invoking directly).
- artifacts: none

- tool: apply_patch (control-ui/db.py, control-ui/app.py, control-ui/static/index.html, control-ui/static/js/status.js, control-ui/static/js/config.js, control-ui/static/js/presets.js)
- result: Pointed the presets SQLite DB to a workspace-safe default, added a status-tab summary for saved presets, refreshed the presets tab automatically after save/delete, and wired a shared refresh hook so new configs appear immediately across the UI.
- artifacts: none

- tool: shell (`bash -lc "python3 - <<'PY' ..."` database smoke)
- result: Verified the refactored `Database` defaults use the project-local path and support create/list/delete after the UI wiring changes.
- artifacts: none

- tool: apply_patch (control-ui/static/js/api.js)
- result: Fixed the container control calls to match the FastAPI contract—`/api/start` now skips empty JSON bodies and `/api/stop`/`/api/restart` pass the timeout as query params—so start/stop no longer fail with 422 errors.
- artifacts: none

- tool: apply_patch (control-ui/static/js/config.js, control-ui/static/js/status.js)
- result: Wired the UI to the new persistence flow: config/status tabs now consume `status.config`, automatically fall back to the most recent saved preset when the container isn’t running, and display saved settings on the dashboard.
- artifacts: none

- tool: apply_patch (add `.assistant/ai_guidance.md`, update backlog/status, remove legacy CLAUDE.md)
- result: Migrated assistant-facing documentation into `.assistant/ai_guidance.md` with accurate compose references and embedded-URL notes, and marked P-001/P-002 completed.
- artifacts: `.assistant/ai_guidance.md`

- tool: apply_patch (matomo-load-baked/tests/test_choose_action_pages.py, test_ecommerce_orders.py, test_events.py)
- result: Expanded pytest coverage to include ecommerce order generation, event definition sanity checks, and updated action ordering guarantees (P-003).
- artifacts: none

- tool: apply_patch (`tools/validate_config.py`, README.md, .assistant/backlog.md, .assistant/status.md)
- result: Added CLI configuration validator with README instructions, marked backlog items P-003/P-004 complete, and recorded the new artifact in status.
- artifacts: tools/validate_config.py

- tool: shell (`python3 -m pytest matomo-load-baked/tests`)
- result: Pytest not installed in environment (`ModuleNotFoundError: pytest`); tests not executed—install dev dependencies to run locally.
- artifacts: none

- tool: apply_patch (matomo-load-baked/tests/test_choose_action_pages.py, dev-requirements.txt)
- result: Adjusted tests to load `loader.py` via importlib and added `pytz` to dev dependencies so pytest can import the module cleanly.
- artifacts: none

- tool: apply_patch (matomo-load-baked/tests/test_ecommerce_orders.py)
- result: Corrected ecommerce test to compare numeric revenue bounds (float) instead of strings.
- artifacts: none

- tool: apply_patch (presets/.env.light, presets/.env.medium, presets/.env.heavy, presets/README.md, README.md, .assistant/backlog.md, .assistant/status.md)
- result: Added CLI-friendly Light/Medium/Heavy preset env files with documentation, updated README instructions, and marked P-005 complete.
- artifacts: presets/.env.light, presets/.env.medium, presets/.env.heavy, presets/README.md

- tool: shell (`python3 -m pytest matomo-load-baked/tests`)
- result: All tests passing (11 total) after installing dev requirements.
- artifacts: none
