# ADR-009: Multi-Target Architecture for P-008

**Status:** Proposed  
**Date:** 2025-11-01  
**Deciders:** System Architect, Backend Team  
**Related:** [GitHub Issue #8](https://github.com/Puttrix/Trafficinator/issues/8)

---

## Context

The Trafficinator load generator currently supports sending traffic to a single Matomo instance. Users have requested the ability to distribute load across multiple Matomo instances concurrently to:

- Test multi-tenant SaaS deployments
- Validate high-availability and failover configurations
- Simulate realistic distributed architectures
- Perform scalability testing across multiple endpoints

The implementation must maintain backward compatibility with existing single-target configurations while enabling new multi-target use cases.

---

## Decision

### 1. Data Model: Embedded JSON Array

**Decision:** Store target configurations as a JSON array within the existing `config_presets` table rather than creating a separate `targets` table.

**Rationale:**
- **Simplicity:** Single source of truth for configuration
- **Atomicity:** Targets and their parent config remain consistent
- **Migration:** Easier to convert single `MATOMO_URL` → first target in array
- **Versioning:** Configuration snapshots include targets automatically

**Schema:**
```python
class Target(BaseModel):
    """Single Matomo tracking target"""
    name: str  # Human-friendly label (e.g., "Production EU", "Staging")
    url: HttpUrl
    site_id: int
    token_auth: Optional[str] = None
    weight: int = 1  # For weighted distribution
    enabled: bool = True

class ConfigEnvironment(BaseModel):
    # Existing fields...
    
    # NEW: Multi-target support (mutually exclusive with MATOMO_URL)
    targets: Optional[List[Target]] = None
    distribution_strategy: Literal["round-robin", "weighted", "random"] = "round-robin"
```

**Backward Compatibility:**
- If `MATOMO_URL` is set → single-target mode (existing behavior)
- If `targets` array is set → multi-target mode (new behavior)
- Validation ensures mutual exclusivity

---

### 2. Distribution Strategies

**Implemented Strategies:**

1. **Round-Robin (default):** Cycle through targets sequentially, ignoring weights
2. **Weighted:** Probability proportional to target weights (e.g., 70% → target A, 30% → target B)
3. **Random:** Uniform random selection across enabled targets

**Implementation:**
```python
class TargetRouter:
    def __init__(self, targets: List[Target], strategy: str):
        self.targets = [t for t in targets if t.enabled]
        self.strategy = strategy
        self.index = 0  # For round-robin
        
    def next_target(self) -> Target:
        if self.strategy == "round-robin":
            target = self.targets[self.index % len(self.targets)]
            self.index += 1
            return target
        elif self.strategy == "weighted":
            return random.choices(self.targets, weights=[t.weight for t in self.targets])[0]
        else:  # random
            return random.choice(self.targets)
```

---

### 3. Concurrency Pattern: AsyncIO + HTTPX

**Decision:** Use `asyncio` with `httpx.AsyncClient` for concurrent request distribution.

**Rationale:**
- Native async/await support
- HTTP/2 multiplexing for efficiency
- Built-in connection pooling
- Timeout and retry handling

**Pattern:**
```python
async def send_tracking_request(
    client: httpx.AsyncClient,
    target: Target,
    params: Dict[str, Any]
) -> TargetResult:
    try:
        response = await client.get(
            f"{target.url}/matomo.php",
            params=params,
            timeout=10.0
        )
        return TargetResult(target=target.name, status=response.status_code)
    except Exception as e:
        return TargetResult(target=target.name, error=str(e))

async def distribute_pageview(targets: List[Target], params: Dict):
    async with httpx.AsyncClient(http2=True) as client:
        # Send to all targets concurrently
        tasks = [send_tracking_request(client, t, params) for t in targets]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
```

---

### 4. Failure Handling: Partial Success Model

**Decision:** Continue visit simulation even if some targets fail; track per-target metrics.

**Rationale:**
- **Resilience:** One failing target shouldn't stop all traffic
- **Observability:** Per-target success/failure rates inform debugging
- **Realistic:** Mirrors production scenarios where some instances may be degraded

**Behavior:**
- Track success/failure per target per request
- Log warnings for failed targets (not errors)
- Dashboard displays per-target health (green/yellow/red)
- Retry logic: 2 retries with exponential backoff (500ms, 1000ms)

**Metrics:**
```python
class TargetMetrics:
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_latency_ms: float
    last_error: Optional[str]
    last_success: Optional[datetime]
```

---

### 5. Configuration Persistence

**Decision:** Extend existing `config_presets` table; no schema migration needed.

**Rationale:**
- `config_json` column already supports arbitrary JSON
- No breaking changes to existing presets
- Single-target configs remain valid

**Example Preset:**
```json
{
  "targets": [
    {
      "name": "Production EU",
      "url": "https://eu.matomo.example.com",
      "site_id": 1,
      "token_auth": "abc123",
      "weight": 70,
      "enabled": true
    },
    {
      "name": "Production US",
      "url": "https://us.matomo.example.com",
      "site_id": 1,
      "token_auth": "def456",
      "weight": 30,
      "enabled": true
    }
  ],
  "distribution_strategy": "weighted",
  "TARGET_VISITS_PER_DAY": "20000"
}
```

---

### 6. UI Design: Dynamic Target List Editor

**Components:**

1. **Mode Selector:** Toggle between "Single Target" and "Multi-Target"
2. **Target List:** Add/remove targets dynamically
3. **Per-Target Fields:** Name, URL, Site ID, Token, Weight, Enabled checkbox
4. **Strategy Selector:** Dropdown for round-robin/weighted/random
5. **Test All Button:** Validate connectivity for all targets before starting
6. **Status Dashboard:** Per-target cards with metrics (requests, success rate, latency)

**Validation:**
- At least one enabled target required
- URL format validation per target
- Weight > 0 for weighted distribution
- Unique target names within a configuration

---

## Consequences

### Positive

- ✅ **Scalability:** Test deployments with multiple Matomo instances
- ✅ **Flexibility:** Support round-robin, weighted, and random distribution
- ✅ **Observability:** Per-target metrics for debugging
- ✅ **Backward Compatible:** Existing configs continue to work
- ✅ **Performance:** AsyncIO enables concurrent requests without blocking

### Negative

- ⚠️ **Complexity:** More configuration options increase cognitive load
- ⚠️ **Testing:** Requires multi-instance test environments
- ⚠️ **Failure Modes:** Partial failures require careful handling
- ⚠️ **Migration:** Users need guidance on converting single → multi-target

### Risks

- **Data Integrity:** Ensure targets receive consistent visitor IDs for session continuity
- **Rate Limiting:** Multiple targets may have different rate limits
- **Token Security:** Multiple tokens stored in config; encryption recommended
- **Network Overhead:** Concurrent requests may hit network limits

---

## Alternatives Considered

### Alternative 1: Separate Targets Table

**Rejected Reason:** Adds unnecessary complexity; foreign key relationships complicate config versioning and exports.

### Alternative 2: Sequential (Non-Concurrent) Distribution

**Rejected Reason:** Defeats the purpose of multi-target support; users want parallel load distribution for realistic testing.

### Alternative 3: Docker Compose with Multiple Generator Containers

**Rejected Reason:** Operational overhead; harder to coordinate and monitor. Multi-target within a single container is more elegant.

---

## Implementation Notes

### Phase 1: Backend Models (Current)
- Extend Pydantic models with `Target` and multi-target fields
- Add validation for mutual exclusivity (single vs. multi)
- Update config validator to handle target arrays

### Phase 2: Loader Changes
- Refactor `send_tracking_request()` to accept target parameter
- Implement `TargetRouter` for distribution logic
- Add async concurrency with `httpx.AsyncClient`
- Track per-target metrics in memory

### Phase 3: UI Updates
- Multi-target mode toggle in config form
- Dynamic target editor (add/remove rows)
- Strategy selector dropdown
- Per-target status cards in dashboard

### Phase 4: Documentation & Testing
- Migration guide for single → multi-target
- Integration tests with mock Matomo servers
- Load testing with 3+ targets
- README examples

---

## References

- [GitHub Issue #8](https://github.com/Puttrix/Trafficinator/issues/8)
- [httpx Async Documentation](https://www.python-httpx.org/async/)
- [asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
- [Pydantic V2 Validation](https://docs.pydantic.dev/latest/)
