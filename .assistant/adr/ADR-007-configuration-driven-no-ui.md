# ADR-007: Configuration-Driven Design (No Control UI)

**Status:** Accepted  
**Date:** 2025-09-10  
**Deciders:** Putte Arvfors  
**Tags:** architecture, simplicity, decision

---

## Context
During development, we explored adding a web-based control UI with:
- REST API endpoints (GET /status, POST /start, POST /stop)
- Configuration form with validation
- Load presets (Light/Medium/Heavy)
- Real-time logs and status monitoring

This would have provided easier configuration and monitoring, especially for non-technical users.

## Decision
**Postpone/reject the control UI indefinitely** in favor of pure configuration-driven design:
- Configuration via environment variables only
- No web interface or REST API
- Docker Compose controls start/stop
- Logs viewed via `docker compose logs`

## Rationale

### Complexity vs. Value
- Adding web UI would require:
  - Separate control service (FastAPI/Express)
  - State management and persistence
  - Security/authentication layer
  - Additional documentation and support
- Maintenance burden for single-person project
- Most users comfortable with Docker Compose already

### Target Audience
- Primary users: DevOps engineers, Matomo admins
- Audience comfortable with YAML configuration
- Docker Compose provides sufficient control
- Advanced users prefer code/config over UI

### Simplicity Wins
- Current approach: Edit YAML, run `docker compose up`
- Proposed: UI adds layer without clear benefit
- Easier to maintain, test, and document
- Aligns with Docker-first philosophy (ADR-001)

## Consequences

### Positive
- **Lower maintenance** — One less service to maintain
- **Simpler architecture** — Configuration via env vars only
- **Better for automation** — Easy to template and version control
- **Faster development** — Focus on core generator features
- **Clearer scope** — Remains a focused tool

### Negative
- **Steeper learning curve** — Users must understand Docker Compose
- **Less discoverable** — No UI to explore options
- **No presets UI** — Can't easily switch between Light/Medium/Heavy
- **Manual log checking** — No web-based log viewer

### Mitigations
- Excellent README with examples
- Multiple compose file examples (dev, prod, test)
- Clear environment variable documentation
- Validation scripts for configuration testing (P-004)

## Alternatives Considered

### 1. Build Full Control UI (Rejected)
- **Pros:** Easier for non-technical users, better discoverability
- **Cons:** Maintenance burden, complexity, security concerns
- **Verdict:** Not worth investment for current user base

### 2. Minimal Status API (Rejected)
- **Idea:** Just GET /status endpoint, no control
- **Pros:** Lighter weight than full UI
- **Cons:** Still adds complexity, unclear value
- **Verdict:** Users can check logs with Docker commands

### 3. CLI Tool (Considered)
- **Idea:** Command-line wrapper around compose
- **Pros:** Scriptable, easier than memorizing compose commands
- **Cons:** Another abstraction layer, wouldn't work in Portainer
- **Verdict:** Docker Compose CLI is sufficient

### 4. Web UI as Separate Project (Future)
- **Idea:** Community-driven UI project as optional add-on
- **Pros:** Separates concerns, optional for those who want it
- **Cons:** Coordination overhead, fragmentation
- **Verdict:** Possible future direction if demand emerges

## Parked Work
Full task list preserved in `.codex/webui-parked.md` for potential future reference.

## Open Questions
- **Q1:** Will users request control UI features? (See status.md)
- **Q7:** Should this be reconsidered with community growth?
- Would a separate community-driven UI project make sense?

## Related Decisions
- Reinforces Docker-first architecture (ADR-001)
- Supports configuration-driven philosophy
- Aligns with single-maintainer reality

## References
- `.codex/webui-parked.md` — Detailed feature list (parked)
- `.codex/memory.md` — Discussion and decision history
- README.md — Configuration documentation
- canvas/questions.md — Q1 about control API
