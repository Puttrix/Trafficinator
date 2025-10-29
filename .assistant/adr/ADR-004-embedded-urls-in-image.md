# ADR-004: Embedded URLs in Docker Image

**Status:** Accepted  
**Date:** 2025-09-01  
**Deciders:** Putte Arvfors  
**Tags:** deployment, simplicity, usability

---

## Context
Originally, `config/urls.txt` was mounted as an external volume. This created:
- Extra deployment step (upload config file)
- Potential for missing/misconfigured URLs
- Confusion about where URLs come from
- Need to document file upload in deployment guide

For production deployments (especially Portainer), users wanted:
- Zero-config deployment (paste compose file and go)
- No separate file uploads needed
- Guaranteed consistent URL set

## Decision
**Embed URLs directly in the Docker image:**
- Move `config/urls.txt` into the image at build time
- Generate 2,000 URLs with 3-level hierarchy
- Remove volume mount from compose files
- URLs become immutable per image version

## Consequences

### Positive
- **Zero external dependencies** — No file uploads needed
- **Portainer-friendly** — Paste compose YAML and deploy immediately
- **Consistent testing** — Same URLs across all deployments
- **Simpler documentation** — One less step in setup guide
- **Version control** — URLs tied to image version

### Negative
- **Less flexible** — Cannot customize URLs without rebuilding image
- **Larger image** — ~50KB additional size (negligible)
- **URL changes require rebuild** — Cannot hot-swap URL list

### Mitigations
- 2,000 URLs provide excellent diversity for testing
- URLs are generic enough for all use cases
- Future: Could add custom URL support via env var (not prioritized)

## Technical Details

### URL Structure
- **10 main categories**: products, blog, support, company, resources, news, services, solutions, documentation, community
- **5 subcategories each**: e.g., products → hardware, software, accessories, bundles, enterprise
- **40 pages per subcategory**: Total 2,000 URLs

### Build Process
```dockerfile
COPY config/urls.txt /config/urls.txt
```

### Impact on Deployments
- **Before:** Upload `docker-compose.yml` + `config/urls.txt`
- **After:** Upload only `docker-compose.yml`

## Alternatives Considered
1. **Keep external mount** — Rejected: Extra deployment complexity
2. **Generate URLs at runtime** — Rejected: Slower startup, less predictable
3. **Environment variable with URLs** — Rejected: Would be massive env var
4. **Hybrid: Default embedded, optional override** — Deferred: Added complexity without clear user demand

## Related Decisions
- Aligns with Docker-first architecture (ADR-001)
- Supports production deployment workflow (DEPLOYMENT.md)

## References
- `matomo-load-baked/Dockerfile` — COPY instruction
- `config/urls.txt` — URL list (2,000 entries)
- README.md — URL Structure section
- DEPLOYMENT.md — Simplified deployment instructions
