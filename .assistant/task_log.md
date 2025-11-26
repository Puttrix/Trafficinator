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

- tool: shell (`bash -lc "sed -n '620,780p' matomo-load-baked/loader.py"`; `bash -lc "sed -n '100,280p' control-ui/static/js/events.js"`); update backlog
- result: Confirmed the Control UI already supports full custom event management (editor, validation, upload/download, backend endpoints) and marked P-028 complete.
- artifacts: none

- tool: apply_patch (control-ui/db.py, control-ui/models.py, control-ui/app.py)
- result: Implemented funnel data model and CRUD API (P-029A) with SQLite schema updates, Pydantic validators, and authenticated `/api/funnels` endpoints.
- artifacts: none

- tool: shell (`python3 -m pytest matomo-load-baked/tests`)
- result: Regression suite still passes (11 tests) after funnel backend changes.
- artifacts: none

- tool: apply_patch (matomo-load-baked/loader.py, control-ui/models.py, matomo-load-baked/tests/test_funnels.py)
- result: Added funnel execution logic to the loader with probability/priority handling, helper functions for loading JSON configs, and pytest coverage for funnel loading/selection (P-029B).
- artifacts: matomo-load-baked/tests/test_funnels.py

- tool: shell (`python3 -m pytest matomo-load-baked/tests`)
- result: All tests passing (13 total) after funnel execution support.
- artifacts: none

- tool: apply_patch (control-ui/static/index.html, control-ui/static/js/api.js, control-ui/static/js/app.js, control-ui/static/js/funnels.js)
- result: Built Funnels tab with templates, structured step editor, preview/test mode, and API integration (P-029C).
- artifacts: control-ui/static/js/funnels.js

- tool: apply_patch (README.md, WEB_UI_GUIDE.md, docker-compose.webui.yml, tools/export_funnels.py)
- result: Documented funnel workflow, added export CLI, updated compose to share funnel data, and satisfied P-029D documentation requirements.
- artifacts: tools/export_funnels.py

- tool: shell (`sed -n '1,160p' control-ui/static/js/app.js`; `git diff HEAD -- control-ui/static/js/funnels.js`)
- result: Confirmed FunnelsManager is still referenced in `app.js` but the dedicated `funnels.js` module was removed, leaving the UI without event bindings.
- artifacts: none

- tool: shell (`git show HEAD:control-ui/static/js/funnels.js > control-ui/static/js/funnels.js`)
- result: Restored the missing `funnels.js` bundle so the Funnels tab can register its event handlers again.
- artifacts: control-ui/static/js/funnels.js

- tool: shell (`docker compose -f docker-compose.webui.yml build control-ui`; `docker compose -f docker-compose.webui.yml up -d control-ui`; `docker compose -f docker-compose.webui.yml logs control-ui --tail 20`)
- result: Rebuilt and restarted the Control UI container; verified clean startup with static assets mounted and API responding.
- artifacts: none

- tool: shell (`curl http://localhost:8000/static/js/funnels.js`)
- result: Confirmed the running Control UI serves the restored `funnels.js` asset.
- artifacts: /tmp/funnels.js

- tool: shell (`docker compose -f docker-compose.webui.yml ps`; `docker ps -a --filter name=matomo-loadgen`; `docker rm matomo-loadgen`; `docker compose -f docker-compose.webui.yml up -d matomo-loadgen`; `docker inspect matomo-loadgen --format '{{json .State.Health}}'`; `docker exec matomo-loadgen env | grep MATOMO`)
- result: Found the load generator container stuck in Created state blocking Compose, removed it, restarted the service, and confirmed it now runs (healthcheck failing due to placeholder MATOMO_URL).
- artifacts: none

- tool: apply_patch (matomo-load-baked/loader.py; matomo-load-baked/debug_build_requests.py; docker-compose.webui.yml)
- result: Loader now resolves URLs from `/app/data/urls.txt` when present (falling back to defaults) and web UI compose sets `URLS_FILE` to the shared data volume so Control UI edits take effect.
- artifacts: none

- tool: shell (`python3 -m pytest matomo-load-baked/tests`)
- result: Regression suite still passes after loader URL resolution changes.
- artifacts: none

- tool: shell (`docker compose -f docker-compose.webui.yml build matomo-loadgen`; `docker rm -f matomo-loadgen`; `docker compose -f docker-compose.webui.yml up -d matomo-loadgen`; `docker exec matomo-loadgen env | grep URL`; `docker exec matomo-loadgen head -n 5 /app/data/urls.txt`)
- result: Rebuilt and redeployed load generator with updated loader/env; confirmed container now reads `/app/data/urls.txt` (shared with Control UI) containing custom URLs.
- artifacts: none

- tool: apply_patch (control-ui/db.py; control-ui/app.py)
- result: Added automatic funnel export support—CRUD operations now write enabled funnels to `/app/data/funnels.json` using shared volume.
- artifacts: control-ui/data/funnels.json (generated at runtime)

- tool: apply_patch (README.md; WEB_UI_GUIDE.md)
- result: Documentation now reflects automatic funnel syncing and optional CLI export workflow.
- artifacts: none

- tool: shell (`python3 -m pytest matomo-load-baked/tests`)
- result: Regression suite still passes after funnel export changes (13 tests).
- artifacts: none

- tool: shell (`docker compose -f docker-compose.webui.yml build control-ui`; `docker compose -f docker-compose.webui.yml up -d --no-deps control-ui`; `curl -s -X PUT .../api/funnels/2`; `docker compose -f docker-compose.webui.yml restart matomo-loadgen`)
- result: Rebuilt/restarted Control UI, verified API update triggers funnel export (funnels.json present), and recycled load generator to load the new funnel definitions.
- artifacts: control-ui/data/funnels.json

- tool: shell (`mkdir -p control-ui/static/img && cp logo.png control-ui/static/img/logo.png`)
- result: Added Trafficinator logo to the static asset directory for use in the UI header.
- artifacts: control-ui/static/img/logo.png

- tool: apply_patch (control-ui/static/index.html)
- result: Rebranded header/title to “Trafficinator” and displayed the logo in the Control UI.
- artifacts: none

- tool: apply_patch (control-ui/static/index.html)
- result: Updated footer “Documentation” link to the public Trafficinator repository.
- artifacts: none

- tool: apply_patch (control-ui/static/index.html)
- result: Made the Trafficinator logo always visible by removing the mobile-only `hidden` class.
- artifacts: none

## 2025-11-26
- tool: apply_patch (.assistant/status.md)
- result: Refreshed status.md from backlog/task_log to reflect current P-008 focus, risks, artifacts, and recent progress.
- artifacts: .assistant/status.md

- tool: apply_patch (matomo-load-baked/loader.py; control-ui/config_validator.py; control-ui/static/index.html; control-ui/static/js/presets.js; control-ui/static/js/config.js; control-ui/static/js/funnels.js; presets/.env.light; presets/.env.medium; presets/.env.heavy)
- result: Defaulted timezone to CET and ecommerce currency to SEK while keeping overrides: updated loader/env defaults, Control UI defaults/placeholders and validation copy, preset definitions and env files, funnel currency placeholder, and ensured currency is always sent in ecommerce payloads.
- artifacts: matomo-load-baked/loader.py, control-ui/config_validator.py, control-ui/static/index.html, control-ui/static/js/presets.js, control-ui/static/js/config.js, control-ui/static/js/funnels.js, presets/.env.light, presets/.env.medium, presets/.env.heavy

- tool: apply_patch (presets/.env.extreme; presets/README.md)
- result: Added file-based Extreme Load preset matching the UI definition (100k/day, concurrency 300, CET/SEK defaults) and documented it alongside existing presets.
- artifacts: presets/.env.extreme, presets/README.md
