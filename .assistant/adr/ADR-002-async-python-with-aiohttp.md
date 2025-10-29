# ADR-002: Async Python with aiohttp

**Status:** Accepted  
**Date:** 2025-08 (retroactive)  
**Deciders:** Putte Arvfors  
**Tags:** architecture, performance, concurrency

---

## Context
The load generator needs to:
- Handle 50+ concurrent HTTP requests efficiently
- Generate 20,000+ visits per day (high throughput)
- Maintain low resource usage
- Simulate realistic timing between requests

## Decision
Use **asyncio + aiohttp** as the foundation:
- `asyncio` for concurrency management
- `aiohttp` for async HTTP client
- Single-threaded event loop with non-blocking I/O
- Token-bucket algorithm for rate limiting

## Consequences

### Positive
- High concurrency with low resource overhead
- Natural fit for I/O-bound workload (HTTP requests)
- Easy to implement timing delays with `asyncio.sleep()`
- Single event loop simplifies reasoning about state
- Excellent scalability (50+ concurrent connections)

### Negative
- Async code is more complex than synchronous
- Debugging async issues can be challenging
- Requires understanding of asyncio patterns
- Cannot use blocking libraries without adaptation

### Trade-offs
- Chose simplicity over distributed architecture
- Single container can handle 20k-50k visits/day
- For higher loads, would need multi-container setup (future: P-012)

## Technical Details

### Concurrency Model
```python
# Token bucket rate limiting
async def generate_visits():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for _ in range(CONCURRENCY):
            task = generate_single_visit(session)
            tasks.append(asyncio.create_task(task))
        await asyncio.gather(*tasks)
```

### Performance Characteristics
- 50 concurrent connections (configurable)
- 0.5-2.0 second pauses between pageviews
- Graceful handling of slow Matomo responses
- Non-blocking shutdown via signal handlers

## Alternatives Considered
1. **Threading** — Rejected: Higher overhead, GIL limitations
2. **Multiprocessing** — Rejected: Too complex for single-container deployment
3. **Sync requests** — Rejected: Cannot achieve target concurrency efficiently
4. **Twisted/Tornado** — Rejected: `asyncio` is Python standard, better ecosystem

## References
- `matomo-load-baked/loader.py` — Core async implementation
- `aiohttp` dependency in requirements.txt
- README.md — Concurrency configuration documentation
