# Web UI Implementation Roadmap

**Decision Date:** 2025-10-29  
**Based on:** P-007 Feasibility Study - Option 1 (Full Web UI)  
**Total Tasks:** 12 (P-015 to P-026)  
**Core Effort:** 56 hours  
**Optional Enhancements:** 12 hours  

---

## Overview

Building a full-featured web UI for Trafficinator with:
- **Backend:** FastAPI REST API + Docker SDK integration
- **Frontend:** Vanilla JS/HTML/CSS + Tailwind CSS
- **Features:** Config form, presets, status dashboard, log viewer
- **Security:** API key auth, CORS, rate limiting, input validation

---

## Phase 1: Backend Foundation (18h)

Core API infrastructure and Docker integration.

### P-015: FastAPI Service Setup (6h)
**Goal:** Get FastAPI service running with Docker SDK integration

**Deliverables:**
- FastAPI app on port 8000
- Docker SDK connected to matomo-loadgen container
- Health check endpoint
- Docker Compose service definition
- Basic container start/stop/query capability

**Files to Create:**
```
control-ui/
├── app.py              # FastAPI application
├── docker_client.py    # Docker SDK wrapper
├── requirements.txt    # FastAPI, docker, uvicorn
└── Dockerfile          # UI service container
```

**Docker Compose:**
```yaml
services:
  control-ui:
    build: ./control-ui
    ports:
      - "8000:8000"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
```

---

### P-016: Core REST API Endpoints (8h)
**Goal:** Implement main control and monitoring endpoints

**Endpoints:**
- `GET /api/status` - Container state, config, runtime stats
- `POST /api/start` - Start generator with config JSON
- `POST /api/stop` - Stop generator gracefully
- `POST /api/restart` - Restart with new config
- `GET /api/logs?lines=N&filter=text` - Fetch container logs

**Response Formats:**
```json
// GET /api/status
{
  "state": "running|stopped|error",
  "config": {...},
  "stats": {
    "uptime": "2h 15m",
    "visits_generated": 1523,
    "rate": "0.23/sec"
  }
}
```

**Files to Update:**
```
control-ui/
├── app.py              # Add endpoints
├── models.py           # Pydantic models for requests/responses
└── container_manager.py # Container control logic
```

---

### P-017: Validation & Testing (4h)
**Goal:** Add config validation and Matomo connectivity check

**Endpoints:**
- `POST /api/validate` - Validate config JSON
- `POST /api/test-connection` - Test Matomo URL

**Validation Rules:**
- Required fields: MATOMO_URL, MATOMO_SITE_ID
- Conditional: MATOMO_TOKEN_AUTH required if RANDOMIZE_VISITOR_COUNTRIES=true
- Numeric ranges: CONCURRENCY > 0, probabilities 0-1
- URL format validation

**Integration:**
- Reuse P-004 validation logic if available
- Return detailed error messages with field names

**Files to Create:**
```
control-ui/
└── validators.py       # Config validation logic
```

---

## Phase 2: Backend Completion & Frontend Core (28h)

Complete backend features and build frontend UI.

### P-018: Configuration Persistence (4h)
**Goal:** Save and load configurations

**Endpoints:**
- `GET /api/configs` - List all saved configs
- `POST /api/configs` - Save new config
- `PUT /api/configs/:id` - Update config
- `DELETE /api/configs/:id` - Delete config
- `GET /api/configs/:id` - Load specific config

**Database:**
- SQLite for simplicity
- Schema: id, name, config_json, created_at, updated_at

**Files to Create:**
```
control-ui/
├── database.py         # SQLite setup and queries
└── crud.py             # CRUD operations for configs
```

---

### P-019: Authentication & Security (6h)
**Goal:** Secure the API and protect sensitive data

**Features:**
- API key authentication (via header or env var)
- CORS configuration for frontend
- Rate limiting (e.g., 100 req/min per IP)
- Input sanitization
- Secure token handling (no MATOMO_TOKEN_AUTH in logs)

**Implementation:**
```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY = os.getenv("CONTROL_UI_API_KEY", "change-me")
api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(key: str = Security(api_key_header)):
    if key != API_KEY:
        raise HTTPException(401, "Invalid API key")
```

**Files to Create:**
```
control-ui/
├── security.py         # Auth middleware
└── rate_limiter.py     # Rate limiting logic
```

**Documentation:**
- Security best practices in README
- How to set API key
- CORS configuration options

---

### P-020: Frontend Foundation (6h)
**Goal:** Create responsive UI layout

**Structure:**
```html
<!DOCTYPE html>
<html>
<head>
  <title>Trafficinator Control Panel</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body>
  <nav><!-- Config | Status | Logs | Presets --></nav>
  <main id="app"><!-- Tab content --></main>
  <script src="/static/js/app.js"></script>
</body>
</html>
```

**Features:**
- Responsive layout (desktop + mobile)
- Tab navigation
- Loading spinners
- Error toast notifications
- Reusable UI components

**Files to Create:**
```
control-ui/static/
├── index.html
├── css/
│   └── styles.css      # Custom styles
└── js/
    ├── app.js          # Main application
    ├── api.js          # API client wrapper
    └── components.js   # UI components
```

---

### P-021: Configuration Form (8h)
**Goal:** Build interactive config form with validation

**Form Sections:**
1. **Core Settings** - URL, Site ID, Token Auth
2. **Traffic Generation** - Visits/day, pageviews, concurrency
3. **Features** - Site search, outlinks, downloads, events, ecommerce
4. **Advanced** - Timezone, geolocation, daily cap, auto-stop

**Features:**
- Real-time client-side validation
- Help text tooltips for each field
- Conditional fields (e.g., token auth visibility)
- Save/Load buttons
- Test Connection button with loading state
- Form reset button

**JavaScript:**
```javascript
// Validation example
function validateConfig(config) {
  const errors = [];
  if (!config.MATOMO_URL) {
    errors.push({field: 'MATOMO_URL', message: 'Required'});
  }
  if (config.RANDOMIZE_VISITOR_COUNTRIES && !config.MATOMO_TOKEN_AUTH) {
    errors.push({field: 'MATOMO_TOKEN_AUTH', message: 'Required when country randomization enabled'});
  }
  return errors;
}
```

---

### P-023: Status Dashboard (6h)
**Goal:** Real-time status monitoring and control

**Dashboard Elements:**
- **State Indicator:** Running (green) / Stopped (gray) / Error (red)
- **Control Buttons:** Start / Stop / Restart (with confirmation)
- **Current Config:** Display active configuration
- **Runtime Metrics:**
  - Uptime: "2h 15m 32s"
  - Visits Generated: 1,523
  - Current Rate: "0.23/sec"
  - Daily Cap Status: "1,523 / 10,000 (15.2%)"
- **Auto-refresh:** Poll API every 5 seconds

**Interactions:**
```javascript
async function loadStatus() {
  const status = await api.getStatus();
  updateUI(status);
  setTimeout(loadStatus, 5000); // Auto-refresh
}

async function startGenerator() {
  if (!confirm('Start load generator?')) return;
  await api.start(currentConfig);
  showSuccess('Generator started');
}
```

---

### P-024: Log Viewer (4h)
**Goal:** View and filter container logs

**Features:**
- Display last N lines (50/100/500/1000)
- Real-time updates (poll every 2 sec when running)
- Filter by level (INFO/WARNING/ERROR)
- Search by text
- Auto-scroll toggle
- Copy to clipboard button
- Clear display button

**UI:**
```
┌─────────────────────────────────────┐
│ Lines: [50] [100] [500] [1000]     │
│ Filter: [____search____] [x]       │
│ Level: [All] [INFO] [WARN] [ERROR] │
│ [Auto-scroll ✓] [Copy] [Clear]    │
├─────────────────────────────────────┤
│ [2025-10-29 14:32:01] Starting...  │
│ [2025-10-29 14:32:02] Loaded URLs  │
│ [2025-10-29 14:32:03] Visit #1... │
└─────────────────────────────────────┘
```

---

## Phase 3: Integration & Polish (12h)

### P-022: Load Presets (4h)
**Goal:** Quick-start templates for common scenarios

**Presets:**
```javascript
const PRESETS = {
  light: {
    TARGET_VISITS_PER_DAY: "1000",
    CONCURRENCY: "10",
    // ... other settings
  },
  medium: {
    TARGET_VISITS_PER_DAY: "10000",
    CONCURRENCY: "30",
  },
  heavy: {
    TARGET_VISITS_PER_DAY: "50000",
    CONCURRENCY: "75",
  }
};
```

**UI:**
- Dropdown selector
- Preview preset values
- Apply to form button
- Save custom preset

**Integration:** Uses P-005 preset definitions

---

### P-025: Testing & Documentation (8h)
**Goal:** Production-ready release

**Testing:**
- Integration tests for all API endpoints
- Browser testing (Chrome, Firefox, Safari, Edge)
- Mobile responsive testing
- Error scenario testing
- Load testing (concurrent requests)

**Documentation:**
- Installation guide
- Configuration reference
- Security setup (API key, CORS)
- Troubleshooting guide
- Screenshots for README
- OpenAPI/Swagger docs

**Files to Create:**
```
control-ui/
├── tests/
│   ├── test_api.py
│   ├── test_container.py
│   └── test_security.py
└── docs/
    ├── API.md
    ├── SETUP.md
    └── SECURITY.md
```

**Deployment:**
```yaml
# docker-compose.webui.yml
version: '3.8'
services:
  matomo-loadgen:
    # ... existing config
  
  control-ui:
    build: ./control-ui
    ports:
      - "8000:8000"
    environment:
      CONTROL_UI_API_KEY: ${API_KEY}
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./control-ui/data:/data
```

**ADR:**
- Create ADR-008 documenting decision to build UI (reversal of ADR-007)

---

## Phase 4: Optional Enhancements (12h)

### P-026: Advanced Features (12h)
**Optional nice-to-haves for future iterations**

**Features:**
- WebSocket for real-time log streaming (no polling)
- Metrics graphs (Chart.js) showing visits over time
- Multi-target orchestration UI
- Export/import configurations (JSON download)
- Dark mode toggle
- Keyboard shortcuts
- User preferences in localStorage

**Prioritization:** Implement based on user feedback after core release

---

## Getting Started

### Recommended Order

**Week 1-2: Backend Core**
1. Start with P-015 (FastAPI setup)
2. Move to P-016 (API endpoints)
3. Finish with P-017 (validation)
4. Test backend thoroughly

**Week 3: Backend Completion**
5. Add P-018 (persistence)
6. Secure with P-019 (auth/security)

**Week 4-5: Frontend**
7. Build P-020 (layout)
8. Create P-021 (config form)
9. Add P-023 (status dashboard)
10. Implement P-024 (log viewer)

**Week 6: Integration**
11. Polish P-022 (presets)
12. Complete P-025 (testing & docs)

**Later: Enhancements**
13. Optional P-026 based on feedback

---

## Success Criteria

### Minimum Viable Product (MVP)
- ✅ Backend API operational (P-015, P-016, P-017)
- ✅ Config form with validation (P-021)
- ✅ Status dashboard with controls (P-023)
- ✅ Basic security (P-019)
- ✅ Documentation (P-025)

### Production Ready
- ✅ All Phase 1-3 tasks complete
- ✅ Browser tested
- ✅ Security audit passed
- ✅ User documentation comprehensive
- ✅ Docker Compose deployment tested

### Feature Complete
- ✅ All core + optional features
- ✅ Community feedback incorporated
- ✅ Performance optimized
- ✅ Accessibility reviewed

---

## Risk Mitigation

**Security:** Start with P-019 early, security review before release  
**Complexity:** Keep frontend vanilla JS (no framework complexity)  
**Testing:** Write tests alongside features, not at end  
**Scope Creep:** MVP first, enhancements later based on feedback  
**Maintenance:** Good documentation = easier long-term support

---

**Next Step:** Start with P-015 (FastAPI service setup)
