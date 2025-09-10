## 2025-09-10 — CLAUDE.md cross-check and doc sync

- Context: Reviewed `CLAUDE.md` for insights to capture and discrepancies to track.
- Decisions/Notes:
  - Architecture confirmations: Docker-first, asyncio/aiohttp, token-bucket rate limiting, graceful shutdown via signal handlers (`CLAUDE.md:98`). Keep core load behavior unchanged; control UI should prefer `docker compose stop` over `down` for graceful exits.
  - Geolocation reminder: `RANDOMIZE_VISITOR_COUNTRIES` requires `MATOMO_TOKEN_AUTH` (`CLAUDE.md:75,103,113`). Surface this in the UI validation and in `POST /test-connection` logic.
  - Doc mismatch: `docker-compose.loadgen.yml` referenced in `CLAUDE.md` (`CLAUDE.md:13,19`), but repo uses `docker-compose.yml` and `docker-compose.prod.yml`. Plan to align docs.
  - URLs source: `CLAUDE.md` mentions `config/urls.txt` as external file (`CLAUDE.md:20`), but current README says URLs are embedded in the image. Keep README as source of truth; update `CLAUDE.md` accordingly.
- Next Steps:
  - Update `CLAUDE.md` to reference `docker-compose.yml`/`docker-compose.prod.yml` and note embedded URLs.
  - Ensure control UI form fields match the envs listed in `CLAUDE.md`/README (traffic, probabilities, ecom, timezone).
  - In status endpoint, reflect graceful-stop semantics and surface daily-cap pause detection from logs.
- References:
  - `CLAUDE.md:13` — envs file naming (“docker-compose.loadgen.yml”).
  - `CLAUDE.md:19` — key components listing.
  - `CLAUDE.md:20` — `config/urls.txt` mention (stale vs README).
  - `CLAUDE.md:75,103,113` — geolocation/token requirements.
  - `CLAUDE.md:98` — graceful shutdown.

## 2025-09-10 — Control UI + Backlog seeded

- Context: New feature branch; capture ideas for decoupled control UI and preserve decisions.
- Decisions:
  - Keep core load logic untouched; if needed, expose a minimal runner facade (`run_load(config)`, `stop_load()`).
  - Add a separate `control_ui` web service in Docker Compose (FastAPI or Node/Express) instead of bundling UI into the generator image.
  - Provide REST endpoints: `GET /status`, `POST /start`, `POST /stop`, `POST /test-connection`.
  - Persist a small config via a mounted volume (e.g., `./config/ui`) to store a `.env` or override used by compose.
  - Detect daily-cap pauses via the log line documented in README rather than coupling to internals.
  - Added `BACKLOG.md` and linked it from README for visibility.
- Open Questions:
  - Backend choice for control service: FastAPI vs Node/Express.
  - Exact presets mapping (Light/Medium/Heavy) to env values.
  - Start semantics: `docker compose up -d` vs restart strategy when config changes; stop via `stop` or `down`.
- Next Steps:
  - Scaffold `control_ui` service and minimal endpoints (hardcoded responses at first).
  - Add optional `control_ui` service block to dev compose (commented in prod).
  - Implement connection test and presets; wire status/log tailing and daily-cap detection.
- References:
  - `BACKLOG.md:1` — Full backlog and tasks.
  - `README.md:472` — Roadmap / Backlog link.
  - `docker-compose.prod.yml:1` — Current prod compose; control UI will be separate or commented.
- Notes:
  - Keep generator image lean; control UI remains optional and decoupled.

## 2025-09-10 — Policy: Treat CLAUDE.md as advisory

- Context: User clarified CLAUDE.md may contain outdated content.
- Decision:
  - Consider `CLAUDE.md` non-authoritative; prefer `README.md`, `docker-compose.yml`, and `docker-compose.prod.yml` as sources of truth.
  - Migrate useful ideas/constraints from `CLAUDE.md` into `.codex/memory.md` and `BACKLOG.md`.
  - Do not modify `CLAUDE.md` just to align; only fix if it causes confusion.

## 2025-09-10 — Decision: Web UI postponed; tasks parked

- Context: We decided to skip/remove the Web UI for now.
- Actions:
  - Removed `control_ui` scaffold and compose stub.
  - Pruned all Web UI content from `BACKLOG.md`.
  - Parked the full UI task list in `.codex/webui-parked.md` for future reference.
- Notes:
  - Backlog is generator-focused; future UI work should be tracked separately.
