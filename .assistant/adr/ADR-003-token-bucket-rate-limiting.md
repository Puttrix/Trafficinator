# ADR-003: Token-Bucket Rate Limiting

**Status:** Accepted  
**Date:** 2025-08 (retroactive)  
**Deciders:** Putte Arvfors  
**Tags:** algorithm, performance, traffic-generation

---

## Context
Need to generate visits at a target rate (e.g., 20,000/day) while:
- Maintaining smooth distribution across 24 hours
- Avoiding traffic spikes that might overload Matomo
- Allowing natural variation in request timing
- Supporting configurable concurrency

## Decision
Implement **token-bucket algorithm** for rate limiting:
- Calculate visit rate from `TARGET_VISITS_PER_DAY`
- Distribute visits evenly across 24 hours
- Use token bucket to smooth request flow
- Add random pauses between pageviews for realism

## Consequences

### Positive
- Smooth, predictable traffic distribution
- Avoids overwhelming Matomo with bursts
- Easy to configure via single parameter (`TARGET_VISITS_PER_DAY`)
- Natural fit with async/await concurrency model
- Gracefully handles varying Matomo response times

### Negative
- Not optimal for burst traffic testing
- Cannot simulate traffic spikes easily
- May under-utilize available capacity during slow periods

### Trade-offs
- Prioritized steady-state testing over burst scenarios
- Chose simplicity over sophisticated traffic patterns
- Future enhancement: Add burst mode (not yet prioritized)

## Technical Details

### Rate Calculation
```python
TARGET_VISITS_PER_DAY = 20000
visits_per_second = TARGET_VISITS_PER_DAY / 86400  # ~0.23 visits/sec
delay_between_visits = 1.0 / visits_per_second    # ~4.32 seconds
```

### Additional Realism
- Random pauses between pageviews: `PAUSE_BETWEEN_PVS_MIN` to `PAUSE_BETWEEN_PVS_MAX`
- Extended visit durations: `VISIT_DURATION_MIN` to `VISIT_DURATION_MAX` minutes
- Natural variation in pageviews per visit: `PAGEVIEWS_MIN` to `PAGEVIEWS_MAX`

### Daily Cap Support
Added per-24-hour window support via `MAX_TOTAL_VISITS`:
- Pause when daily cap reached
- Resume when 24-hour window resets
- Allows indefinite running with controlled daily volume

## Alternatives Considered
1. **Fixed interval scheduling** — Rejected: Too rigid, unrealistic
2. **Poisson distribution** — Rejected: Added complexity without clear benefit for our use case
3. **Reactive rate limiting** — Rejected: Would require monitoring Matomo's capacity
4. **Burst mode** — Deferred: May add as future enhancement (not in backlog yet)

## Open Questions
- **Q2:** Is this optimal for all scenarios? (See status.md)
- Should we add burst mode for spike testing?

## References
- `matomo-load-baked/loader.py` — Token-bucket implementation
- README.md — `TARGET_VISITS_PER_DAY` configuration
- README.md — Daily cap behavior section
