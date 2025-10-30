# ADR-008: Full Web Control UI Implementation

**Status:** Accepted  
**Date:** 2025-10-29  
**Deciders:** Putte Arvfors  
**Tags:** architecture, web-ui, decision-reversal

---

## Context

On 2025-09-10, we made the decision to postpone/reject the web control UI (ADR-007) in favor of pure configuration-driven design. At that time, the rationale focused on:

- Maintenance burden for single-person project
- Target audience comfortable with Docker Compose
- Simplicity and focus on core features

**Two months later, circumstances have changed:**

1. **User Feedback:** Multiple requests for easier configuration and monitoring capabilities
2. **Operational Need:** Real-time visibility into load generator status became increasingly important
3. **Technical Maturity:** Core generator features are stable and well-tested
4. **FastAPI Availability:** Modern framework makes UI development straightforward
5. **Security Model:** Simple API key authentication is sufficient for target use cases

## Decision

**Build a full-featured web control UI** with:

- **FastAPI backend** serving REST API and static files
- **Responsive web interface** with Tailwind CSS
- **4-tab interface:**
  - Status Dashboard - Real-time monitoring
  - Configuration Form - GUI-based config management
  - Load Presets - One-click scenario selection
  - Log Viewer - Live log streaming with filtering
- **API key authentication** for security
- **Rate limiting** to prevent abuse
- **Docker-based deployment** via docker-compose.webui.yml

This represents a **reversal of ADR-007**.

## Rationale

### User Experience Improvements

**1. Lower Barrier to Entry**
- No need to understand Docker Compose syntax
- Visual feedback on configuration validity
- Discoverable features through UI exploration
- Test connection before starting load generation

**2. Operational Visibility**
- Real-time container status (running/stopped/error)
- Live log streaming without SSH access
- Quick access to current configuration
- Visual indicators for system state

**3. Configuration Safety**
- Form validation prevents invalid configurations
- Warnings for high-load settings
- Test connection verifies Matomo accessibility
- Load presets provide battle-tested configurations

### Technical Feasibility

**1. Lightweight Implementation**
- FastAPI provides auto-generated OpenAPI docs
- Tailwind CSS CDN eliminates build process
- Vanilla JavaScript keeps frontend simple
- Single-file app.py for backend logic

**2. Security Built-In**
- API key authentication (constant-time comparison)
- Rate limiting per endpoint (10-60 req/min)
- Security headers (HSTS, X-Frame-Options, etc.)
- CORS configuration for production

**3. Minimal Maintenance**
- No database (stateless API)
- Docker SDK handles container operations
- Pydantic provides validation
- Static file serving by FastAPI

### Operational Benefits

**1. Multi-User Scenarios**
- Web UI accessible to team members
- No SSH access needed
- Centralized control point
- Audit trail via logs

**2. Monitoring Integration**
- Health check endpoint for uptime monitoring
- Status API for external dashboards
- Structured JSON responses for automation
- Rate-limited to prevent overload

**3. Deployment Simplicity**
- Single docker-compose.webui.yml file
- Environment-based configuration
- Automatic restarts via Docker
- Easy to add to existing deployments

## Consequences

### Positive

- **Improved UX** — Much easier to configure and monitor
- **Better visibility** — Real-time status and logs
- **Lower barrier** — Non-technical users can operate it
- **Operational safety** — Validation prevents misconfigurations
- **Team-friendly** — Multiple users can access UI
- **Well-documented** — Comprehensive user guide and security docs

### Negative

- **Additional service** — One more container to maintain
- **Security surface** — Web API adds attack vectors
- **Complexity** — ~2500 lines of code added
- **Testing burden** — Browser compatibility, API tests
- **Documentation** — User guide, security best practices needed

### Mitigations

- **Security:** API key auth, rate limiting, security headers, CORS
- **Maintenance:** Simple architecture, comprehensive tests, good docs
- **Complexity:** Well-structured code, clear separation of concerns
- **Testing:** Automated integration tests, browser compatibility verified

## Technical Implementation

### Architecture

```
┌─────────────────────────────────────────┐
│         User Browser                     │
│  ┌─────────────────────────────────┐   │
│  │  Tailwind CSS UI (4 tabs)       │   │
│  │  - Status Dashboard              │   │
│  │  - Configuration Form            │   │
│  │  - Load Presets                  │   │
│  │  - Log Viewer                    │   │
│  └──────────┬──────────────────────┘   │
└─────────────┼───────────────────────────┘
              │ HTTP/HTTPS + API Key
              ▼
┌─────────────────────────────────────────┐
│    control-ui (FastAPI)                  │
│  ┌──────────────────────────────────┐   │
│  │  REST API                         │   │
│  │  - Authentication middleware      │   │
│  │  - Rate limiting (slowapi)        │   │
│  │  - Docker SDK integration         │   │
│  │  - Config validation (Pydantic)   │   │
│  └──────────┬───────────────────────┘   │
└─────────────┼───────────────────────────┘
              │ Docker API
              ▼
┌─────────────────────────────────────────┐
│    matomo-loadgen (Container)            │
│  - Generator process                     │
│  - Configuration via env vars            │
│  - Docker-managed logs                   │
└─────────────────────────────────────────┘
```

### Key Components

**Backend (control-ui/):**
- `app.py` (421 lines) - FastAPI application, middleware, endpoints
- `models.py` (102 lines) - Pydantic models for validation
- `docker_client.py` (160 lines) - Docker SDK wrapper
- `container_manager.py` (238 lines) - Container lifecycle management
- `config_validator.py` (356 lines) - Configuration validation logic
- `auth.py` (51 lines) - API key authentication

**Frontend (control-ui/static/):**
- `index.html` - Single-page application structure
- `js/api.js` (134 lines) - API client with auth handling
- `js/ui.js` (180 lines) - UI helper functions
- `js/config.js` (436 lines) - Configuration form management
- `js/status.js` (414 lines) - Status dashboard
- `js/presets.js` (371 lines) - Load preset system
- `js/logs.js` (323 lines) - Log viewer with filtering
- `js/app.js` (140 lines) - Application controller

**Documentation:**
- `WEB_UI_GUIDE.md` - Comprehensive user guide
- `SECURITY.md` - Security best practices
- `control-ui/test_setup.py` - Integration tests

### API Endpoints

| Endpoint | Method | Auth | Rate Limit | Purpose |
|----------|--------|------|------------|---------|
| /health | GET | No | - | Health check |
| /api/status | GET | Yes | 60/min | Container status |
| /api/start | POST | Yes | 10/min | Start container |
| /api/stop | POST | Yes | 10/min | Stop container |
| /api/restart | POST | Yes | 10/min | Restart container |
| /api/logs | GET | Yes | 30/min | Retrieve logs |
| /api/validate | POST | Yes | 30/min | Validate config |
| /api/test-connection | POST | Yes | 20/min | Test Matomo |

### Security Features

1. **Authentication**
   - API key via X-API-Key header
   - Constant-time comparison prevents timing attacks
   - Configurable via CONTROL_UI_API_KEY env var

2. **Rate Limiting**
   - Per-endpoint limits (10-60 req/min)
   - IP-based tracking via slowapi
   - 429 responses with Retry-After headers

3. **Security Headers**
   - X-Content-Type-Options: nosniff
   - X-Frame-Options: DENY
   - X-XSS-Protection: 1; mode=block
   - Strict-Transport-Security (if HTTPS)

4. **CORS**
   - Configurable origins (default: *)
   - Credentials support
   - Preflight caching

## Deployment Model

### Development
```bash
docker-compose -f docker-compose.webui.yml up -d
# Access: http://localhost:8000/ui
```

### Production
```yaml
# docker-compose.prod.yml
services:
  control-ui:
    image: trafficinator-control-ui:latest
    environment:
      CONTROL_UI_API_KEY: "${API_KEY}"
      CORS_ORIGINS: "https://dashboard.example.com"
    networks:
      - internal
    ports:
      - "127.0.0.1:8000:8000"  # Localhost only
```

Recommended: Deploy behind reverse proxy (nginx, Caddy, Traefik) with HTTPS.

## Alternatives Considered

### 1. Keep Configuration-Only Approach (ADR-007)
- **Pros:** Simpler, no additional services
- **Cons:** Poor UX, limited visibility, steep learning curve
- **Verdict:** User feedback indicated strong need for UI

### 2. Minimal Status API Only
- **Idea:** Just GET /status endpoint, no configuration
- **Pros:** Lighter than full UI
- **Cons:** Doesn't address configuration pain point
- **Verdict:** Half-measure, build full solution or nothing

### 3. Third-Party Tools (Portainer, Dozzle)
- **Idea:** Use existing Docker management tools
- **Pros:** No development needed
- **Cons:** Generic, not tailored to Trafficinator workflow
- **Verdict:** Doesn't provide load preset or validation features

### 4. CLI Tool
- **Idea:** Command-line wrapper for docker-compose
- **Pros:** Scriptable, no web server
- **Cons:** Still requires technical knowledge, no remote access
- **Verdict:** Doesn't solve multi-user or remote access scenarios

### 5. Desktop Application (Electron)
- **Idea:** Native desktop app
- **Pros:** Rich UI, no browser needed
- **Cons:** Platform-specific builds, distribution complexity
- **Verdict:** Overkill for target use case

## Success Criteria

**Phase 1: Core Functionality (✅ Complete)**
- [x] FastAPI service with REST API
- [x] Docker SDK integration
- [x] Configuration validation
- [x] API authentication
- [x] Rate limiting

**Phase 2: Web Interface (✅ Complete)**
- [x] Responsive UI with Tailwind CSS
- [x] Status dashboard with real-time updates
- [x] Configuration form with validation
- [x] Load presets (Light/Medium/Heavy/Extreme)
- [x] Log viewer with filtering

**Phase 3: Polish & Documentation (🚧 In Progress)**
- [x] Integration tests
- [x] Browser compatibility
- [x] OpenAPI documentation
- [x] User guide (WEB_UI_GUIDE.md)
- [ ] Screenshots/GIFs for README
- [x] Security best practices (SECURITY.md)
- [x] Deployment verification
- [x] ADR-008 documentation

## Future Enhancements (Optional)

**Phase 4 Candidates:**
- WebSocket support for true real-time log streaming
- Metrics graphs (visits over time, success rate)
- Multi-target orchestration (manage multiple instances)
- Configuration import/export
- Dark mode toggle
- User preferences persistence
- Keyboard shortcuts

**P-018 (Deferred):**
- SQLite database for saved configurations
- CRUD API for configuration management
- Extend presets to user-saved configs

## Relationship to Other ADRs

- **Reverses:** ADR-007 (Configuration-Driven Design)
- **Builds on:** ADR-001 (Docker-First Architecture)
- **Complements:** ADR-003 (Rate Limiting)
- **Extends:** Adds web layer to existing generator

## Open Questions

- **Q1:** Will the web UI increase support burden?
  - **Mitigation:** Comprehensive documentation, integration tests
  
- **Q2:** Should we support multi-tenancy?
  - **Answer:** No - single-tenant model sufficient for current scope
  
- **Q3:** How to handle configuration persistence?
  - **Answer:** Deferred to P-018, current approach is stateless

- **Q4:** What about mobile support?
  - **Answer:** Responsive design works on tablets, phone support nice-to-have

## Lessons Learned

1. **User feedback matters** - Original decision was technically sound but ignored user needs
2. **Modern frameworks reduce burden** - FastAPI made this much easier than anticipated
3. **Security first** - Building auth/rate-limiting from start was correct
4. **Documentation is critical** - User guide and security docs as important as code
5. **Iteration works** - Building in phases (backend → frontend → polish) was effective

## References

- ADR-007 (Reversed) - Configuration-Driven Design
- P-015 to P-024 - Web UI implementation tasks in BACKLOG.md
- WEB_UI_GUIDE.md - User documentation
- SECURITY.md - Security best practices
- control-ui/test_setup.py - Integration test suite
- .assistant/WEB_UI_ROADMAP.md - Original implementation plan

---

**Approval:** Accepted  
**Implementation:** Complete (Phases 1-2), In Progress (Phase 3)  
**Review Date:** 2026-01-01 (assess user adoption and support burden)
