# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Trafficinator is a Matomo load testing tool built with Python and Docker. It generates realistic web traffic by simulating user visits with multiple pageviews to test Matomo analytics performance.

## Architecture

- **Docker-based**: Uses Docker Compose for orchestration with a lightweight Python Alpine container
- **Async Python**: Built with `asyncio` and `aiohttp` for high-concurrency HTTP requests
- **Configuration-driven**: All parameters controlled via environment variables in `docker-compose.loadgen.yml`
- **Load generation**: Token-bucket algorithm for smooth traffic distribution with configurable concurrency

### Key Components

- `matomo-load-baked/loader.py` - Main load generator script (183 lines)
- `docker-compose.loadgen.yml` - Service configuration and environment variables
- `config/urls.txt` - Target URLs for load testing (large file with test URLs)
- `matomo-load-baked/Dockerfile` - Container build configuration

## Development Commands

### Running the Load Generator
```bash
docker-compose up --build
```

### Stop and Clean Up
```bash
docker-compose down
```

### View Logs
```bash
docker-compose logs -f matomo_loadgen
```

### Rebuild Container
```bash
docker-compose build --no-cache
```

## Configuration

All configuration is done via environment variables in `docker-compose.yml`:

- `MATOMO_URL` - Target Matomo installation endpoint
- `MATOMO_SITE_ID` - Site ID in Matomo to track
- `TARGET_VISITS_PER_DAY` - Desired daily visit rate
- `PAGEVIEWS_MIN/MAX` - Range of pageviews per visit
- `CONCURRENCY` - Number of concurrent connections
- `PAUSE_BETWEEN_PVS_MIN/MAX` - Timing between pageviews
- `AUTO_STOP_AFTER_HOURS` - Auto-stop timer (0 = disabled)
- `MAX_TOTAL_VISITS` - Visit limit before stopping (0 = disabled)

## Key Patterns

- Uses realistic user agents rotation
- Implements proper visit tracking with visitor IDs
- Graceful shutdown handling with signal handlers
- Rate limiting with token-bucket algorithm
- Auto-stop functionality for controlled test runs
- Health checks for container monitoring

## Dependencies

- Python 3.11 Alpine base image
- `aiohttp==3.9.5` for async HTTP requests
- Standard library: `asyncio`, `random`, `signal`, `time`