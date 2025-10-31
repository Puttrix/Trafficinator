# Trafficinator Web UI User Guide

Complete guide for using the Trafficinator Web Control Interface.

---

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [User Interface](#user-interface)
  - [Status Tab](#user-interface)
  - [Config Tab](#user-interface)
  - [Presets Tab](#user-interface)
  - [Logs Tab](#4-logs-tab)
  - [URLs Tab](#5-urls-tab)
  - [Events Tab](#6-events-tab)
  - [Funnels Tab](#7-funnels-tab)
- [API Reference](#api-reference)
- [Security](#security)
- [Troubleshooting](#troubleshooting)

---

## Overview

The Trafficinator Web UI provides a modern, browser-based interface for controlling and monitoring the Matomo load generator. Features include:

- **Real-time Status Dashboard** - Monitor container state, uptime, and metrics
- **Configuration Management** - Easy form-based configuration with validation
- **Load Presets** - Quick access to 4 pre-configured load scenarios
- **Live Log Viewing** - Real-time log streaming with filtering and search
- **URL Management** - Edit URL list directly via Web UI
- **Container Control** - Start, stop, and restart operations
- **REST API** - Full programmatic access for automation

---

## Installation

### Prerequisites

- Docker and Docker Compose
- Port 8000 available (or configure a different port)
- Modern web browser (Chrome, Firefox, Safari, or Edge)

### Quick Start

1. **Start the Web UI service:**
   ```bash
   docker-compose -f docker-compose.webui.yml up -d
   ```

2. **Access the UI:**
   Open your browser to: [http://localhost:8000/ui](http://localhost:8000/ui)

3. **Set API Key (first time):**
   You'll be prompted to enter an API key. Use the default:
   ```
   change-me-in-production
   ```
   
   Or set a custom key in `docker-compose.webui.yml`:
   ```yaml
   environment:
     CONTROL_UI_API_KEY: "your-secure-key-here"
   ```

### Production Deployment

For production use, always set a secure API key:

```yaml
# docker-compose.webui.yml
services:
  control-ui:
    environment:
      CONTROL_UI_API_KEY: "${CONTROL_UI_API_KEY}"  # From .env file
```

Create `.env`:
```bash
CONTROL_UI_API_KEY="your-long-random-secure-key"
```

---

## Getting Started

### First Launch

1. Navigate to http://localhost:8000/ui
2. Enter your API key when prompted (stored in browser localStorage)
3. You'll land on the **Status** tab showing current container state

### Basic Workflow

1. **Configure** - Set up your Matomo target and load parameters
2. **Test Connection** - Verify connectivity before starting
3. **Start** - Begin generating traffic
4. **Monitor** - Watch status and logs in real-time
5. **Stop** - Halt traffic generation when done

---

## User Interface

The Web UI consists of 5 main tabs:

### 1. Status Tab

**Purpose:** Real-time monitoring of the load generator.

**Features:**
- **Status Indicator** - Visual state (running/stopped/error)
  - 🟢 Green (pulsing) = Running
  - ⚪ Gray = Stopped
  - 🟡 Yellow = Starting/Paused
  - 🔴 Red = Error
- **Control Buttons**
  - Start - Begin traffic generation
  - Stop - Halt traffic generation (10s timeout)
  - Restart - Stop and restart container
- **Metrics Cards**
  - Container uptime
  - Total visits (placeholder - shows 0)
  - Current rate (placeholder - shows 0/sec)
  - Daily target progress
- **Current Configuration** - Shows 9 key config values
- **Auto-refresh** - Updates every 5 seconds

**Usage:**
```
1. Click Start to begin generating traffic
2. Monitor the uptime and status indicator
3. Click Stop when finished
4. Use Restart to apply configuration changes
```

### 2. Config Tab

**Purpose:** Configure load generator parameters.

**Features:**
- **25+ Configuration Fields** organized in sections:
  - **Matomo Connection** - URL, Site ID, Token Auth
  - **Load Parameters** - Daily visits, pageviews, concurrency
  - **Visit Behavior** - Duration, pauses, probabilities
  - **E-commerce** - Order values, currency
  - **System** - Timezone, auto-stop, limits
- **Real-time Validation** - Instant feedback on invalid values
- **Test Connection** - Verify Matomo accessibility
- **Conditional Fields** - E-commerce fields appear when enabled
- **Warning Indicators** - Shows warnings for high-load configs

**Usage:**
```
1. Fill in Matomo URL (e.g., https://analytics.example.com/matomo.php)
2. Enter Site ID (numeric)
3. Add Token Auth if required (optional for tracking APIs)
4. Set Target Visits Per Day (default: 20,000)
5. Click "Test Connection" to verify
6. Adjust other parameters as needed
7. Click "Apply Configuration" to save
8. Restart container for changes to take effect
```

**Field Reference:**

| Field | Description | Default | Range |
|-------|-------------|---------|-------|
| MATOMO_URL | Matomo tracking endpoint | Required | Valid URL ending in .php |
| MATOMO_SITE_ID | Site identifier | Required | 1-999999 |
| MATOMO_TOKEN_AUTH | Authentication token | Optional | 32+ chars |
| TARGET_VISITS_PER_DAY | Daily visit target | 20000 | 100-200000 |
| PAGEVIEWS_MIN | Min pages per visit | 1 | 1-50 |
| PAGEVIEWS_MAX | Max pages per visit | 5 | 1-50 |
| CONCURRENCY | Parallel visitors | 5 | 1-50 |
| PAUSE_BETWEEN_PVS_MIN | Min pause (seconds) | 3 | 0-3600 |
| PAUSE_BETWEEN_PVS_MAX | Max pause (seconds) | 10 | 0-3600 |

### 3. Presets Tab

**Purpose:** Quick load testing scenarios.

**Features:**
- **4 Pre-configured Presets**
  - 🌱 **Light** - 5K visits/day, low concurrency
  - 🏃 **Medium** - 20K visits/day, standard load
  - 🚀 **Heavy** - 50K visits/day, high throughput
  - 💥 **Extreme** - 100K visits/day, stress testing
- **One-Click Loading** - Instantly apply preset configuration
- **Preserved Settings** - Matomo URL, Site ID, and Token Auth retained
- **Visual Selection** - Clear indicators showing active preset

**Usage:**
```
1. Click on a preset card
2. Confirm the configuration change
3. Preset values are applied to Config tab
4. Restart container for changes to take effect
```

**Preset Details:**

| Preset | Visits/Day | Concurrency | Pageviews | Use Case |
|--------|------------|-------------|-----------|----------|
| Light | 5,000 | 2 | 1-3 | Development testing |
| Medium | 20,000 | 5 | 1-5 | Standard load testing |
| Heavy | 50,000 | 10 | 1-8 | High-traffic simulation |
| Extreme | 100,000 | 20 | 2-10 | Stress/capacity testing |

### 4. Logs Tab

**Purpose:** View and analyze container logs in real-time.

**Features:**
- **Configurable Line Count** - View 50, 100, 500, or 1000 lines
- **Live Auto-refresh** - Updates every 2 seconds
- **Search Filtering** - Text search across log content
- **Color-coded Levels**
  - 🔴 Red = ERROR
  - 🟡 Yellow = WARNING
  - 🔵 Blue = INFO
  - ⚪ Gray = DEBUG
- **Auto-scroll** - Automatically follow new log entries
- **Copy to Clipboard** - One-click log export
- **Clear Display** - Reset view without affecting container

**Usage:**
```
1. Select line count (default: 100)
2. Click Refresh to load logs
3. Use search box to filter
4. Enable auto-refresh for live monitoring
5. Toggle auto-scroll to follow new entries
6. Click Copy to save logs
```

**Statistics Display:**
- Total lines in container logs
- Filtered lines (after search)
- Container status

---

### 5. URLs Tab

**Purpose:** Manage the URL list that defines which pages the load generator visits.

**Features:**
- **URL Editor** - Edit URLs directly in the browser
- **Live Validation** - Check URL format and structure
- **File Upload** - Import URLs from .txt files
- **Download** - Export current URL list
- **Reset to Defaults** - Restore embedded URL list
- **Structure Preview** - View category distribution and statistics
- **Format Support**
  - One URL per line
  - Optional page titles: `URL<TAB>Title`
  - Comments: Lines starting with `#`
  - Blank lines ignored

**Usage:**
```
1. Click Refresh to load current URLs
2. Edit URLs in the textarea editor
3. Click Validate to check format
4. Review validation results and structure
5. Click Save to upload new URLs
6. Restart container to apply changes
```

**Validation Results:**
- ✅ Valid/Invalid status
- URL count
- List of errors (if any)
- List of warnings (if any)

**Structure Preview:**
- Total URLs
- Categories count
- Subcategories count
- Unique domains
- Category distribution graph

**URL Sources:**
The load generator checks three locations in order:
1. `/app/data/urls.txt` - Custom URLs (uploaded via UI)
2. `/config/urls.txt` - Mounted from host
3. Embedded `config/urls.txt` - Default URLs baked into container

**Note:** After uploading custom URLs or resetting to defaults, you must restart the container for changes to take effect.

---

### 6. Events Tab

**Purpose:** Manage Matomo events (clicks, random interactions) generated during load tests.

**Highlights:**
- JSON editor with validation and probability controls
- Upload/download support for sharing event configurations
- Inline statistics preview for quick sanity checks
- Reset to defaults when you need a clean slate

> **Note:** Saving changes requires restarting the generator because events are loaded at startup.

### 7. Funnels Tab

**Purpose:** Build deterministic user journeys that complement random browsing.

**Workflow:**
1. **Create or edit** a funnel using the structured step editor (pageviews, events, site search, outlinks, downloads, ecommerce).
2. **Preview** the journey to validate ordering and delays.
3. **Export** funnels for the loader:
   ```bash
   python tools/export_funnels.py --api-base http://localhost:8000 --api-key <key> --output control-ui/data/funnels.json
   docker compose -f docker-compose.webui.yml restart matomo-loadgen
   ```

**Tips:**
- Probability controls how often a funnel executes; priority resolves ordering when multiple funnels match.
- “Exit after completion” switches visitors back to random browsing once the funnel finishes.

Use the built-in templates (Ecommerce, Lead Generation, Content Discovery) as a starting point for your own campaigns.

---

## API Reference

The Web UI is powered by a REST API. All endpoints require authentication via `X-API-Key` header.

### Base URL
```
http://localhost:8000
```

### Authentication

Include API key in request header:
```bash
curl -H "X-API-Key: your-api-key-here" \
  http://localhost:8000/api/status
```

### Endpoints

#### GET /health
Health check endpoint (no auth required).

**Response:**
```json
{
  "status": "healthy",
  "docker": "connected",
  "container_found": true,
  "authenticated": true
}
```

#### GET /api/status
Get container status and configuration.

**Rate Limit:** 60 requests/minute

**Response:**
```json
{
  "container": {
    "state": "running",
    "name": "matomo-loadgen",
    "id": "abc123",
    "uptime": "2h 15m",
    "created": "2025-10-29T10:00:00Z",
    "started_at": "2025-10-29T10:00:00Z"
  },
  "config": {
    "MATOMO_URL": "https://analytics.example.com/matomo.php",
    "MATOMO_SITE_ID": "1",
    "TARGET_VISITS_PER_DAY": "20000"
  },
  "stats": {
    "uptime": "2h 15m",
    "visits_generated": null,
    "current_rate": null
  }
}
```

#### POST /api/start
Start the load generator container.

**Rate Limit:** 10 requests/minute

**Request Body (optional):**
```json
{
  "config": {
    "MATOMO_URL": "https://analytics.example.com/matomo.php",
    "MATOMO_SITE_ID": "1",
    "TARGET_VISITS_PER_DAY": "20000"
  },
  "restart_if_running": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Container started successfully",
  "state": "running",
  "error": null
}
```

#### POST /api/stop
Stop the load generator container.

**Rate Limit:** 10 requests/minute

**Query Parameters:**
- `timeout` - Stop timeout in seconds (1-60, default: 10)

**Response:**
```json
{
  "success": true,
  "message": "Container stopped successfully",
  "state": "stopped"
}
```

#### POST /api/restart
Restart the load generator container.

**Rate Limit:** 10 requests/minute

**Query Parameters:**
- `timeout` - Stop timeout in seconds (1-60, default: 10)

**Response:**
```json
{
  "success": true,
  "message": "Container restarted successfully",
  "state": "running"
}
```

#### GET /api/logs
Retrieve container logs.

**Rate Limit:** 30 requests/minute

**Query Parameters:**
- `lines` - Number of lines to retrieve (1-5000, default: 100)

**Response:**
```json
{
  "state": "running",
  "logs": [
    "2025-10-29 10:00:00 INFO Starting load generator",
    "2025-10-29 10:00:01 INFO Generated visit #1"
  ],
  "total_lines": 2,
  "filtered_lines": 2,
  "container_name": "matomo-loadgen"
}
```

#### POST /api/validate
Validate configuration before applying.

**Rate Limit:** 30 requests/minute

**Request Body:**
```json
{
  "matomo_url": "https://analytics.example.com/matomo.php",
  "matomo_site_id": 1,
  "target_visits_per_day": 20000,
  "pageviews_min": 1,
  "pageviews_max": 5
}
```

**Response:**
```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    "High concurrency (10) may impact target system"
  ],
  "config": {
    "matomo_url": "https://analytics.example.com/matomo.php",
    "matomo_site_id": 1
  }
}
```

#### POST /api/test-connection
Test Matomo server connectivity.

**Rate Limit:** 20 requests/minute

**Request Body:**
```json
{
  "matomo_url": "https://analytics.example.com/matomo.php",
  "timeout": 10
}
```

**Response:**
```json
{
  "success": true,
  "message": "Connection successful (HTTP 200, 145ms)",
  "status_code": 200,
  "response_time_ms": 145.3,
  "error": null
}
```

#### GET /api/urls
Get current URL list and validation results.

**Rate Limit:** 20 requests/minute

**Response:**
```json
{
  "content": "https://example.com/page1\nhttps://example.com/page2",
  "source": "custom",
  "validation": {
    "valid": true,
    "url_count": 2,
    "errors": [],
    "warnings": ["Only 2 URLs found. Recommend at least 100."]
  },
  "structure": {
    "total_urls": 2,
    "unique_domains": 1,
    "total_categories": 2,
    "total_subcategories": 2,
    "categories": {"page1": 1, "page2": 1},
    "hierarchy": {...}
  }
}
```

#### POST /api/urls
Upload custom URL list.

**Rate Limit:** 10 requests/minute

**Request Body:**
```json
{
  "content": "https://example.com/page1\nhttps://example.com/page2"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully uploaded 2 URLs. Restart container to apply changes.",
  "validation": {...},
  "structure": {...},
  "restart_required": true
}
```

#### POST /api/urls/validate
Validate URL list without saving.

**Rate Limit:** 20 requests/minute

**Request Body:**
```json
{
  "content": "https://example.com/page1\nhttps://example.com/page2"
}
```

**Response:**
```json
{
  "valid": true,
  "url_count": 2,
  "errors": [],
  "warnings": ["Only 2 URLs found. Recommend at least 100."],
  "structure": {...}
}
```

#### DELETE /api/urls
Reset URLs to defaults (embedded in container).

**Rate Limit:** 10 requests/minute

**Response:**
```json
{
  "success": true,
  "message": "URLs reset to defaults. Restart container to apply changes.",
  "restart_required": true
}
```

### Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| /api/status | 60 | 1 minute |
| /api/logs | 30 | 1 minute |
| /api/start | 10 | 1 minute |
| /api/stop | 10 | 1 minute |
| /api/restart | 10 | 1 minute |
| /api/validate | 30 | 1 minute |
| /api/test-connection | 20 | 1 minute |
| /api/urls (GET) | 20 | 1 minute |
| /api/urls (POST) | 10 | 1 minute |
| /api/urls (DELETE) | 10 | 1 minute |
| /api/urls/validate | 20 | 1 minute |

**Rate Limit Headers:**
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1698585600
```

### Interactive API Documentation

FastAPI provides interactive documentation at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Security

### API Key Authentication

**Required for all `/api/*` endpoints.**

1. Set API key in environment:
   ```yaml
   environment:
     CONTROL_UI_API_KEY: "your-secure-key"
   ```

2. Include in requests:
   ```bash
   curl -H "X-API-Key: your-secure-key" \
     http://localhost:8000/api/status
   ```

3. Browser storage:
   - Key stored in localStorage
   - Persists across sessions
   - Change via UI prompt (Ctrl/Cmd + K)

### Best Practices

1. **Use Strong API Keys**
   ```bash
   # Generate secure key
   openssl rand -base64 32
   ```

2. **Enable HTTPS in Production**
   ```yaml
   # Use reverse proxy (nginx, Caddy, Trafficinator)
   services:
     control-ui:
       labels:
         - "traefik.http.routers.control-ui.tls=true"
   ```

3. **Configure CORS**
   ```yaml
   environment:
     CORS_ORIGINS: "https://dashboard.example.com,https://admin.example.com"
   ```

4. **Network Isolation**
   ```yaml
   # Restrict to internal network
   ports:
     - "127.0.0.1:8000:8000"  # localhost only
   ```

5. **Monitor Rate Limits**
   - Watch for 429 responses
   - Implement backoff in scripts
   - Adjust limits if needed

### Security Headers

Automatically applied to all responses:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains` (if HTTPS)

---

## Troubleshooting

### Cannot Access Web UI

**Problem:** Browser shows "Connection refused"

**Solutions:**
1. Verify container is running:
   ```bash
   docker ps | grep control-ui
   ```

2. Check logs:
   ```bash
   docker logs trafficinator-control-ui
   ```

3. Verify port mapping:
   ```bash
   docker port trafficinator-control-ui
   ```

### API Key Not Accepted

**Problem:** "401 Unauthorized" or "403 Forbidden"

**Solutions:**
1. Check API key is set:
   ```bash
   docker exec trafficinator-control-ui env | grep CONTROL_UI_API_KEY
   ```

2. Verify key in browser:
   - Open Developer Tools > Console
   - Type: `localStorage.getItem('trafficinator_api_key')`

3. Re-enter key:
   - Press Ctrl/Cmd + K
   - Enter correct API key

### Rate Limit Exceeded

**Problem:** "429 Too Many Requests"

**Solutions:**
1. Wait for rate limit to reset (1 minute)
2. Reduce request frequency
3. Use auto-refresh features instead of manual refresh

### Container Won't Start

**Problem:** Start button shows error

**Solutions:**
1. Check Docker daemon:
   ```bash
   docker info
   ```

2. Verify configuration:
   - Go to Config tab
   - Click "Test Connection"
   - Fix any validation errors

3. Check container logs:
   ```bash
   docker logs matomo-loadgen
   ```

4. Restart control UI:
   ```bash
   docker-compose -f docker-compose.webui.yml restart control-ui
   ```

### Logs Not Showing

**Problem:** Logs tab shows "No logs available"

**Solutions:**
1. Verify container exists:
   ```bash
   docker ps -a | grep matomo-loadgen
   ```

2. Check container is running:
   - Go to Status tab
   - Click Start if stopped

3. Increase line count to 500 or 1000

4. Check Docker logs access:
   ```bash
   docker logs matomo-loadgen --tail 10
   ```

### Configuration Not Applied

**Problem:** Changes don't take effect

**Solutions:**
1. Always restart after config changes:
   - Apply Configuration
   - Go to Status tab
   - Click Restart

2. Verify config was saved:
   - Go to Status tab
   - Check "Current Configuration" section

3. Check for validation errors:
   - Red indicators on form fields
   - Error messages below fields

### High Memory/CPU Usage

**Problem:** Control UI consuming excessive resources

**Solutions:**
1. Disable auto-refresh on unused tabs
2. Reduce log line count (use 50-100 instead of 1000)
3. Lower auto-refresh frequency in code
4. Check browser developer tools for errors

---

## Additional Resources

- **Project README:** [README.md](README.md)
- **Deployment Guide:** [DEPLOYMENT.md](DEPLOYMENT.md)
- **API Documentation:** http://localhost:8000/docs
- **Issue Tracker:** [GitHub Issues](https://github.com/Puttrix/Trafficinator/issues)

---

## Version Information

- **Web UI Version:** 1.0.0
- **FastAPI Version:** 0.104.1
- **Supported Browsers:** Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Last Updated:** October 29, 2025
