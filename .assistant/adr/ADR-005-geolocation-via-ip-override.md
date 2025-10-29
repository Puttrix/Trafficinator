# ADR-005: Geolocation via IP Override

**Status:** Accepted  
**Date:** 2025-09-01  
**Deciders:** Putte Arvfors  
**Tags:** feature, realism, matomo-integration

---

## Context
Realistic load testing requires diverse visitor geolocation to:
- Test Matomo's GeoIP database performance
- Populate location reports with realistic data
- Validate region/country-specific analytics
- Ensure reports handle international traffic

Challenges:
- Load generator runs from single server (one IP)
- Cannot easily distribute across global locations
- Need to simulate traffic from multiple countries

## Decision
Use Matomo's **`cip` (Client IP) parameter** to override visitor IP addresses:
- Maintain curated list of real IP ranges from major ISPs/hosting providers
- Distribute visitor countries based on realistic global web traffic patterns
- Require `MATOMO_TOKEN_AUTH` for security (Matomo only accepts IP override with valid token)
- Make feature optional via `RANDOMIZE_VISITOR_COUNTRIES` flag

## Consequences

### Positive
- **Realistic location data** — Tests GeoIP lookups with authentic IPs
- **No infrastructure required** — Single server simulates global traffic
- **Diverse reports** — Populates country/region/city dimensions
- **Authentic IPs** — Uses real ISP/datacenter ranges for accuracy
- **Configurable** — Can disable for simple testing

### Negative
- **Requires API token** — Users must configure `MATOMO_TOKEN_AUTH`
- **Token management** — Tokens can expire or be revoked
- **Security consideration** — IP override is powerful, requires authentication
- **Maintenance** — IP ranges may need updates as ISPs change

### Trade-offs
- Chose realism over simplicity (token requirement)
- Prioritized authentic IPs over simpler fake ranges
- Made feature optional to support simple use cases

## Technical Details

### Country Distribution (Default)
- **United States:** 35% (Google, Facebook, GitHub, Cloudflare, Akamai)
- **Germany:** 10% (Hetzner, Deutsche Telekom, T-Mobile)
- **United Kingdom:** 8% (Microsoft Azure UK, Virgin Media, BT, Sky)
- **Canada:** 6% (Shaw, Rogers, Bell Canada)
- **France:** 6% (Online.net, Scaleway, Orange)
- **Australia:** 5% (Telstra, Optus, TPG)
- **Netherlands:** 5% (TransIP, KPN)
- **Japan:** 4% (Japanese hosting, universities)
- **Sweden:** 3% (Telia, Bredband2, Comhem)
- **Brazil:** 3% (Brazilian ISPs)
- **Other:** 15% (European, Asian, African ranges)

### Security Model
Matomo requires `token_auth` for IP overriding to prevent abuse:
```python
params['cip'] = random_ip_from_country()
params['token_auth'] = MATOMO_TOKEN_AUTH
```

Without token → Matomo rejects with "requires valid token_auth" error

### Configuration
```yaml
RANDOMIZE_VISITOR_COUNTRIES: "true"  # Enable feature
MATOMO_TOKEN_AUTH: "your_token"      # Required when enabled
```

## Alternatives Considered
1. **Fake IP ranges** — Rejected: Would fail GeoIP lookups
2. **Proxy network** — Rejected: Expensive, complex infrastructure
3. **VPN rotation** — Rejected: Slow, unreliable, expensive
4. **Fixed single country** — Rejected: Not realistic for most sites
5. **Country code parameter** — Rejected: Matomo doesn't support direct country override

## Open Questions
- Should we add more countries? (Current: 10+ represented)
- Should IP ranges be configurable via external file?
- Do we need to update IP ranges periodically?

## Related Decisions
- Complements traffic source diversification
- Works with timezone configuration (ADR-006)
- Requires Docker-first architecture for embedded IP lists (ADR-001)

## References
- `matomo-load-baked/loader.py` — IP randomization logic
- README.md — Visitor Geolocation Simulation section
- README.md — Geolocation Setup instructions
- `check_ranges.py` — IP range validation script
