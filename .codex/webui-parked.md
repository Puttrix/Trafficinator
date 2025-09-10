## Web UI — Parked Tasks (2025-09-10)

Context: Web UI is postponed. Keeping tasks here for future reference, removed from `BACKLOG.md`.

- Control service (FastAPI/Express) with endpoints:
  - GET /status, POST /start, POST /stop, POST /test-connection
- Compose integration (separate service `control_ui`), optional persisted `.env` via volume
- UI features:
  - Start/Stop controls
  - Config form with validation (require MATOMO_TOKEN_AUTH when RANDOMIZE_VISITOR_COUNTRIES=true)
  - Presets: Light/Medium/Heavy mapping to envs
  - Status + last N logs, detect daily-cap pause via log line
- Runner facade (optional): `run_load(config)`, `stop_load()` as thin wrappers
- Nice-to-haves: Docker API client, auth, metrics, live logs via SSE/WS, multi-target profiles

References:
- Removed sections from `BACKLOG.md` (Control UI & API, UI Features, related tasks)
- `.codex/memory.md` entries on policy and notes
