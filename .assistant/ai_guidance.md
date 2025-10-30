# AI Assistant Guide

This repository uses the `.assistant/` workspace for planning, status tracking, and documentation targeted at AI coding partners. Use the files here—rather than the legacy `CLAUDE.md`—when you need quick project context.

## Project Snapshot

- **Purpose:** Trafficinator generates realistic traffic against Matomo for load and regression testing.
- **Primary language:** Python (async with `aiohttp`), orchestrated via Docker.
- **Key services:**  
  - `matomo-loadgen` — the generator container, defined in `docker-compose.yml` (development) and `docker-compose.prod.yml` (production/Watchtower).  
  - `trafficator-control-ui` — FastAPI + frontend service exposed through `docker-compose.webui.yml`.
- **Entrypoints:**  
  - `matomo-load-baked/loader.py` — core generator logic.  
  - `control-ui/app.py` — FastAPI + static UI server.

## Docker Compose Files

| File | Scenario | Notes |
|------|----------|-------|
| `docker-compose.yml` | Local development of the generator only | Exposes the CLI-driven workload. |
| `docker-compose.prod.yml` | Remote/production deployment (with Watchtower) | Pulls published image from GHCR; auto-updates. |
| `docker-compose.webui.yml` | Full stack: generator + Control UI | Mounts SQLite data dir for presets, maps UI to port 8000. |

All instructions/docs should reference these filenames (the retired `docker-compose.loadgen.yml` is obsolete).

## Configuration & Presets

- Environment variables are the primary configuration surface; every compose file sets sensible defaults.
- The Docker image now bundles the canonical `urls.txt`. Users no longer upload `config/urls.txt` manually—custom URLs are handled through the Control UI (`/ui`, URLs tab).
- Saved configurations and presets live in `control-ui/data/presets.db` (SQLite) when using the web UI stack.

## Useful Commands

```bash
# Local generator (CLI only)
docker compose up --build

# Web UI stack
docker compose -f docker-compose.webui.yml up -d

# Production deployment
docker compose -f docker-compose.prod.yml up -d
```

## Documentation Pointers

- `.assistant/status.md` — high-level status, risks, next steps.
- `.assistant/backlog.md` — authoritative backlog (P-### items).
- `README.md` / `DEPLOYMENT.md` — user-facing setup and operations.
- `.assistant/task_log.md` — chronological log of assistant actions.

When contributing updates or answering questions, prefer these sources. If you encounter references to `CLAUDE.md`, migrate them into this guide or other `.assistant` docs and treat the legacy file as deprecated.
