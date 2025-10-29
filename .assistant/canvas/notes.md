# Notes / Scratchpad

Sketches, links, snippets. Purge or refactor regularly to docs/.

---

## Ecommerce Design Notes
From `ecommerce_design.md`:

**Matomo Parameters:**
- `idgoal=0` - Required for ecommerce orders
- `ec_id` - Unique order ID
- `ec_items` - JSON array of items
- `revenue` - Total order value
- `ec_st` - Subtotal, `ec_tx` - Tax

**Product Categories:**
Electronics, Clothing, Books, Home & Garden, Sports (50+ products total)

**Purchase Patterns:**
- Single item (60%), Multi-item (35%), High-value (5%)
- Order values: $10-$500 (weighted toward $20-$100)
- Tax: 8-12%, Shipping: $0, $5.99, $9.99, $15.99

---

## Architecture Notes
From `CLAUDE.md`:

**Core Technologies:**
- Docker Compose for orchestration
- Python 3.11 Alpine base
- `asyncio` + `aiohttp` for async HTTP
- Token-bucket algorithm for rate limiting
- Graceful shutdown via signal handlers

**Key Behaviors:**
- Events never as first action in visit
- Proper `urlref` attribution for outlinks/downloads
- Per-24-hour `MAX_TOTAL_VISITS` window with pause/resume
- Country randomization requires `MATOMO_TOKEN_AUTH`

---

## Performance Characteristics
- 20k+ visits/day capability
- 50+ concurrent connections
- 2,000 pre-built URLs in 3-level hierarchy
- Configurable 1-8 minute visit durations

---

## Web UI - Parked
See `.codex/webui-parked.md` for full details
- Control service endpoints (GET /status, POST /start/stop)
- Config UI with validation
- Presets: Light/Medium/Heavy
- Currently postponed - config via environment only
