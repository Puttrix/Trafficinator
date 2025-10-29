# History

Major milestones and evolution of Trafficinator.

---

## 2025-09-10 — Web UI Postponed
**Decision:** Removed experimental `control_ui` scaffold and compose stub. Web UI parked indefinitely.
- Parked tasks moved to `.codex/webui-parked.md`
- Backlog pruned to focus on generator features only
- Decision: Keep tool configuration-driven via environment variables
- **Refs:** `.codex/memory.md`, BACKLOG.md

---

## 2025-09-07 — Behavior Guarantees & Daily Cap
**Enhancement:** Improved event behavior and daily visit cap implementation
- Outlinks, Downloads, Site Search, Custom Events never as first action
- Proper `urlref` attribution for outlinks/downloads
- Relative download paths converted to full URLs
- Per-24-hour `MAX_TOTAL_VISITS` window with pause/resume
- Default config changed to run indefinitely (`restart: unless-stopped`)
- **Commits:** 72a8117, 8e196d3, 9ce96c8
- **Refs:** CHANGELOG.md, README.md (daily cap section)

---

## 2025-09-01 — Ecommerce & Timezone Support
**Major Feature:** Full ecommerce order simulation added
- 50+ products across 5 categories (Electronics, Clothing, Books, Home & Garden, Sports)
- Realistic order patterns: 1-5 items, $15-$299 range
- Tax, shipping, and multi-currency support
- Configurable purchase probability (default 5%)
- Timezone configuration for accurate visit timestamps
- **Commits:** aee2f85
- **Refs:** ecommerce_design.md, README.md (Ecommerce section)

---

## 2025-09-01 — Traffic Sources & Geolocation
**Major Feature:** Realistic traffic source and country distribution
- Search engines (35%): Google, Bing, DuckDuckGo, Yahoo
- Social media (15%): Twitter, LinkedIn, Facebook, Reddit, etc.
- Referral sites (20%): Industry directories and marketing blogs
- Direct traffic (30%): Configurable probability
- Global visitor simulation with authentic IP ranges for 10+ countries
- Requires `MATOMO_TOKEN_AUTH` for IP overriding
- **Commits:** 098821f, 0cea435, 86ba770
- **Refs:** README.md (Traffic Sources, Geolocation sections)

---

## 2025-09-01 — Production Deployment & Auto-Updates
**Infrastructure:** GitHub Container Registry + Watchtower integration
- Docker images auto-built via GitHub Actions
- Watchtower monitors for updates every 30s
- `docker-compose.prod.yml` for production deployments
- Portainer Stack support
- URLs embedded in Docker image (no external config needed)
- **Commits:** 3111f9d, 4e020c6
- **Refs:** DEPLOYMENT.md, README.md (Remote Deployment)

---

## 2025-08-31 — Custom Events Tracking
**Feature:** Comprehensive custom events simulation
- Click events (25%): UI interactions, navigation, forms
- Random events (12%): Engagement, performance, errors
- Rich metadata with categories, actions, names, values
- Proper Matomo compliance (`e_c`, `e_a`, `e_n`, `e_v`)
- **Commits:** 6d35607, 9f47788
- **Refs:** README.md (Custom Events section)

---

## 2025-08-26 — Run Indefinitely by Default
**Enhancement:** Changed default behavior to continuous operation
- `AUTO_STOP_AFTER_HOURS=0` (disabled by default)
- `restart: unless-stopped` for production resilience
- Daily cap feature added for controlled long-running tests
- **Commits:** 6815376, e371fec
- **Refs:** CHANGELOG.md

---

## 2025-08-22 — Action Ordering Guarantees
**Enhancement:** Ensure realistic event sequencing
- Site Search, Outlinks, Downloads, Events never as first action
- Regular pageview always precedes special events
- Improved Matomo's ability to classify events correctly
- **Commit:** 9ce96c8
- **Refs:** README.md (Behavior guarantees section)

---

## Project Genesis
**Initial Release:** Matomo load testing tool with realistic traffic simulation
- Docker-based deployment
- Async Python with `aiohttp`
- Token-bucket rate limiting
- 3-level URL hierarchy (2,000 URLs)
- Configurable concurrency and visit rates
- User agent rotation
- **Core Features:**
  - Multiple pageviews per visit (3-6)
  - Natural timing between requests
  - Extended visit durations (1-8 minutes)
  - 20k+/day capability with 50+ concurrent connections
