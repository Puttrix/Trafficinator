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
