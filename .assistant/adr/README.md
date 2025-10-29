# Architecture Decision Records (ADRs)

This directory contains records of significant architectural decisions made in Trafficinator.

## Index

- **[ADR-001: Docker-First Architecture](ADR-001-docker-first-architecture.md)** — Why we built on Docker/Docker Compose
- **[ADR-002: Async Python with aiohttp](ADR-002-async-python-with-aiohttp.md)** — Concurrency model and HTTP client choice
- **[ADR-003: Token-Bucket Rate Limiting](ADR-003-token-bucket-rate-limiting.md)** — Traffic distribution algorithm
- **[ADR-004: Embedded URLs in Docker Image](ADR-004-embedded-urls-in-image.md)** — Why URLs are built into the image
- **[ADR-005: Geolocation via IP Override](ADR-005-geolocation-via-ip-override.md)** — How we simulate global traffic
- **[ADR-006: Timezone Configuration](ADR-006-timezone-configuration.md)** — Configurable timezone support
- **[ADR-007: Configuration-Driven Design (No Control UI)](ADR-007-configuration-driven-no-ui.md)** — Decision to remain configuration-driven

## Format

Each ADR follows this structure:
```markdown
# ADR-NNN: Title

**Status:** Proposed | Accepted | Rejected | Superseded  
**Date:** YYYY-MM-DD  
**Deciders:** Who decided  
**Tags:** relevant, tags

## Context
What problem are we solving?

## Decision
What did we decide?

## Consequences
### Positive
### Negative
### Trade-offs

## Alternatives Considered
What else did we consider?

## References
Links to related docs, code, issues
```
