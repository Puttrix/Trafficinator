# ADR-006: Timezone Configuration

**Status:** Accepted  
**Date:** 2025-09-01  
**Deciders:** Putte Arvfors  
**Tags:** feature, localization, matomo-integration

---

## Context
Load testing should generate visits with timestamps that reflect the user's operational timezone:
- Users want to see visits in their local time (not always UTC)
- Testing timezone-specific reports and business hour analysis
- Validating Matomo's timezone handling
- Realistic data for regional analytics

Without timezone control:
- All visits appear in UTC
- Doesn't match user's business hours
- Harder to validate time-based reports

## Decision
Add **configurable timezone support via `TIMEZONE` environment variable:**
- Default to UTC for predictable behavior
- Support any valid timezone identifier (e.g., "America/New_York", "Europe/Stockholm")
- Use Matomo's `cdt` (custom datetime) parameter to set visit timestamps
- Apply timezone offset to all visit timestamps

## Consequences

### Positive
- **Accurate local time** — Visits show in user's operational timezone
- **Business hour testing** — Can validate time-based analytics
- **Regional analytics** — Matches local time expectations
- **Flexible configuration** — Single env var controls all timestamps
- **Standard format** — Uses IANA timezone identifiers

### Negative
- **Complexity** — Users must know correct timezone identifier
- **Clock skew risk** — Custom timestamps could conflict with server time
- **Timezone knowledge** — Requires understanding of timezone concepts
- **DST handling** — Must rely on Python's pytz for DST transitions

### Trade-offs
- Chose flexibility over forced UTC
- Prioritized user convenience over simplicity
- Made UTC the safe default

## Technical Details

### Configuration
```yaml
TIMEZONE: "America/New_York"  # Eastern Time
TIMEZONE: "Europe/Stockholm"  # Swedish Time
TIMEZONE: "UTC"               # Default (safe choice)
```

### Implementation
```python
import pytz
from datetime import datetime

tz = pytz.timezone(TIMEZONE)
visit_time = datetime.now(tz)
params['cdt'] = visit_time.isoformat()
```

### Matomo Integration
Uses `cdt` parameter to override visit timestamp:
- Matomo respects custom datetime for all visit data
- Reports show visits in specified timezone
- Time-based segmentation works correctly

## Use Cases
1. **US Business:** Set "America/New_York" to match Eastern business hours
2. **European Operations:** Set "Europe/Stockholm" for Swedish time
3. **Australian Testing:** Set "Australia/Sydney" for local time
4. **Global Default:** Use "UTC" for timezone-agnostic testing

## Alternatives Considered
1. **UTC only** — Rejected: Not convenient for regional testing
2. **Offset-based** (e.g., "+02:00") — Rejected: Doesn't handle DST, less intuitive
3. **Multiple timezones per visit** — Rejected: Over-engineered, unclear value
4. **Auto-detect from geolocation** — Rejected: Too complex, ambiguous mappings

## Open Questions
- Should we provide preset timezone aliases (e.g., "EST" → "America/New_York")?
- Do users need per-visitor timezone randomization?
- Should we validate timezone at startup?

## Related Decisions
- Complements geolocation feature (ADR-005)
- Works with traffic source diversification
- Supports realistic visit simulation

## References
- `matomo-load-baked/loader.py` — Timezone implementation
- README.md — Timezone Configuration section
- Python `pytz` dependency for timezone handling
