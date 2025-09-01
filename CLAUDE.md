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

### Core Settings
- `MATOMO_URL` - Target Matomo installation endpoint
- `MATOMO_SITE_ID` - Site ID in Matomo to track
- `MATOMO_TOKEN_AUTH` - Matomo API token (required for IP overriding when using country randomization)

### Traffic Generation
- `TARGET_VISITS_PER_DAY` - Desired daily visit rate
- `PAGEVIEWS_MIN/MAX` - Range of pageviews per visit
- `CONCURRENCY` - Number of concurrent connections
- `PAUSE_BETWEEN_PVS_MIN/MAX` - Timing between pageviews

### Auto-stop Controls
- `AUTO_STOP_AFTER_HOURS` - Auto-stop timer (0 = disabled)
- `MAX_TOTAL_VISITS` - Visit limit before stopping (0 = disabled)

### Feature Probabilities
- `SITESEARCH_PROBABILITY` - Probability (0-1) that a visit includes site search
- `OUTLINKS_PROBABILITY` - Probability (0-1) that a visit includes outlinks
- `DOWNLOADS_PROBABILITY` - Probability (0-1) that a visit includes downloads
- `CLICK_EVENTS_PROBABILITY` - Probability (0-1) that a visit includes click events
- `RANDOM_EVENTS_PROBABILITY` - Probability (0-1) that a visit includes random events

### Traffic Sources
- `DIRECT_TRAFFIC_PROBABILITY` - Probability (0-1) for direct traffic vs referrer traffic

### Geolocation
- `RANDOMIZE_VISITOR_COUNTRIES` - Enable realistic country distribution (true/false)
  - **Note**: When enabled, requires `MATOMO_TOKEN_AUTH` to be set for IP overriding to work

### Ecommerce Tracking
- `ECOMMERCE_PROBABILITY` - Probability (0-1) that a visit makes a purchase (default: 0.05 = 5%)
- `ECOMMERCE_ORDER_VALUE_MIN/MAX` - Order value range (default: $15.99-$299.99)
- `ECOMMERCE_ITEMS_MIN/MAX` - Items per order range (default: 1-5)
- `ECOMMERCE_TAX_RATE` - Tax rate as decimal (default: 0.10 = 10%)
- `ECOMMERCE_SHIPPING_RATES` - Available shipping costs, comma-separated (default: "0,5.99,9.99,15.99")
- `ECOMMERCE_CURRENCY` - Currency code for orders (default: "USD", format: ISO 4217)

### Localization
- `TIMEZONE` - Timezone for visit timestamps (default: "UTC", examples: "America/New_York", "Europe/Stockholm")

## Key Patterns

- **Realistic traffic simulation**: User agents rotation, referrer sources, country distribution
- **Visit tracking**: Proper visitor IDs and session management
- **Geolocation support**: Randomized country distribution with IP override capability
- **Advanced features**: Site search, outlinks, downloads, custom events, ecommerce orders
- **Ecommerce simulation**: Realistic product catalog with 50+ products across 5 categories, multi-currency support
- **Localization support**: Configurable timezones for accurate timestamp tracking
- **Rate limiting**: Token-bucket algorithm for smooth traffic distribution
- **Graceful shutdown**: Signal handlers for clean container stops
- **Auto-stop functionality**: Time-based and visit-count limits for controlled test runs

## Geolocation Setup

When using `RANDOMIZE_VISITOR_COUNTRIES: "true"`, you need to:

1. **Get your Matomo API token:**
   - Go to Matomo → Personal → Security
   - Copy your API authentication token

2. **Add the token to your environment:**
   ```yaml
   environment:
     MATOMO_TOKEN_AUTH: "your_api_token_here"
     RANDOMIZE_VISITOR_COUNTRIES: "true"
   ```

3. **Restart the container** to apply changes

Without the token, requests with IP overriding will be rejected by Matomo for security reasons.

## Dependencies

- Python 3.11 Alpine base image
- `aiohttp==3.9.5` for async HTTP requests
- Standard library: `asyncio`, `random`, `signal`, `time`