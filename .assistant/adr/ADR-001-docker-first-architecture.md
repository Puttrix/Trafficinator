# ADR-001: Docker-First Architecture

**Status:** Accepted  
**Date:** 2025-08 (retroactive)  
**Deciders:** Putte Arvfors  
**Tags:** architecture, deployment, infrastructure

---

## Context
Trafficinator needed a deployment strategy that:
- Works consistently across different environments (dev, staging, production)
- Minimizes installation complexity for users
- Allows easy updates and version management
- Isolates dependencies from host systems

## Decision
Build Trafficinator as a Docker-first application with:
- **Python 3.11 Alpine base image** for minimal footprint
- **Docker Compose** as primary orchestration
- **All dependencies containerized** (no local Python installation needed)
- **Configuration via environment variables** in compose files
- **Embedded resources** (URLs, config) in the image

## Consequences

### Positive
- Users only need Docker/Docker Compose installed
- Consistent behavior across environments
- Easy to update via image pulls
- Clean separation from host system
- Integrates well with Portainer and other container management tools

### Negative
- Requires Docker knowledge from users
- Slightly more complex debugging than native Python
- Container overhead (minimal with Alpine)
- Cannot easily run partial tests without container

### Mitigations
- Provide clear Docker Compose examples
- Include debugging instructions with LOG_LEVEL
- Keep container lightweight with Alpine base
- Support both dev and prod compose configurations

## Alternatives Considered
1. **Native Python package** — Rejected: Dependency management complexity, environment inconsistencies
2. **Kubernetes-only** — Rejected: Too complex for small deployments, Docker Compose more accessible
3. **Binary distribution** — Rejected: Would require compilation, lose Python flexibility

## References
- `docker-compose.yml` — Development configuration
- `docker-compose.prod.yml` — Production configuration with Watchtower
- `matomo-load-baked/Dockerfile` — Container build definition
- DEPLOYMENT.md — Remote deployment guide
