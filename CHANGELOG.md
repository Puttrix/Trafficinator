# Changelog

## [2.0.0] - 2025-10-29

### Added - Web Control UI 🎨

**Major Release: Full Web Control Interface**

- **Modern Web UI** with responsive design (Tailwind CSS)
  - Status Dashboard with real-time monitoring
  - Configuration Form with 25+ fields and validation
  - Load Presets (Light/Medium/Heavy/Extreme)
  - Live Log Viewer with filtering and search
- **REST API** for programmatic control
  - 7 endpoints: status, start, stop, restart, logs, validate, test-connection
  - API key authentication with constant-time comparison
  - Rate limiting (10-60 req/min per endpoint)
  - Security headers (HSTS, X-Frame-Options, etc.)
  - CORS configuration
- **Docker Deployment**
  - New `docker-compose.webui.yml` for easy setup
  - FastAPI backend (Python 3.11)
  - Static file serving
  - Health check endpoint
- **Documentation**
  - Comprehensive user guide (WEB_UI_GUIDE.md)
  - Security best practices (SECURITY.md)
  - ADR-008 documenting decision to build UI
  - Integration test suite
  - OpenAPI/Swagger documentation at /docs
- **Architecture Decision**
  - Reverses ADR-007 (configuration-only approach)
  - Modern FastAPI + vanilla JavaScript architecture
  - Docker SDK integration for container management
  - Pydantic validation for configuration safety

### Changed

- Updated README with Web UI documentation and API reference
- Added security notes for production deployment
- Enhanced documentation structure with multiple guides

### Technical Details

**Backend (2,500+ lines):**
- FastAPI 0.104.1 with lifespan management
- Docker SDK 6.1.3 for container control
- Pydantic 2.5.0 for validation
- slowapi for rate limiting
- Comprehensive error handling

**Frontend (2,000+ lines):**
- 4-tab SPA (Status/Config/Presets/Logs)
- Tailwind CSS CDN for styling
- Vanilla JavaScript (no build process)
- localStorage for API key persistence
- Auto-refresh and real-time updates

**Security:**
- API key authentication required
- Rate limiting on all endpoints
- Security headers middleware
- Configurable CORS
- Constant-time key comparison

## [1.x.x] - Previous Releases

### Core Features (Established)

- Ensure Outlinks, Downloads and Site Search are never the first action in a visit.
- Set `urlref` for outlink/download hits to the page that contained the link.
- Convert relative download paths to full URLs using the page's base URL.
- Add debug script `matomo-load-baked/debug_build_requests.py` to print constructed Matomo requests.
- Add `choose_action_pages` helper and unit tests.
- Implement per-24-hour `MAX_TOTAL_VISITS` window (generator pauses after daily cap and resumes when 24h window resets).
- Default docker-compose configuration changed to run indefinitely by default (`AUTO_STOP_AFTER_HOURS=0`, `restart: unless-stopped`).
