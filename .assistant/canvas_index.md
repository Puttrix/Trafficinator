# Project Canvas

Strategic planning and design thinking space.

---

## 📂 Canvas Structure

### Core Documents
- **[vision.md](canvas/vision.md)** — Problem statement, target users, success criteria, non-goals
- **[goals.md](canvas/goals.md)** — Short-term (1-2 weeks), mid-term (1-2 months), long-term (quarter+)
- **[stakeholders.md](canvas/stakeholders.md)** — Core team, users, community, expectations

### Exploration
- **[questions.md](canvas/questions.md)** — 11 open questions across architecture, features, deployment, community
- **[ideas.md](canvas/ideas.md)** — Traffic patterns, configuration presets, monitoring, advanced features
- **[notes.md](canvas/notes.md)** — Ecommerce design, architecture notes, performance characteristics, parked features

---

## 🎯 Quick Reference

### Vision Summary
**Trafficinator** is a realistic Matomo load testing tool that helps administrators and DevOps teams:
- Identify performance bottlenecks in Matomo reports
- Validate optimization improvements with controlled tests
- Populate test environments with realistic analytics data

Target: 20k+/day visits with diverse behaviors (search, ecommerce, events, global geolocation)

### Current Goals
- **Now:** Documentation alignment, test coverage
- **Next:** Validation utilities, load presets, user journey improvements
- **Later:** Advanced features (multi-target, k8s, plugins) based on community demand

### Key Stakeholders
- **Creator:** Putte Arvfors ([@Puttrix](https://github.com/Puttrix))
- **Users:** Matomo admins, hosting providers, enterprise teams, DevOps engineers
- **Community:** Open source contributors, Matomo ecosystem

### Top Open Questions
1. Should we add a control API? (Currently parked per ADR-007)
2. Right balance between realism and configurability?
3. What documentation is missing for first-time users?

---

## 📝 Usage

### When to Update Canvas
- **Vision changes** → Update vision.md
- **New goals emerge** → Update goals.md
- **Questions answered** → Move to history or ADR
- **Ideas validated** → Move to backlog
- **Design notes** → Add to notes.md

### Canvas Philosophy
- **Strategic thinking space** — Not tactical/implementation details
- **Living documents** — Update as project evolves
- **Capture uncertainty** — Questions are valuable
- **Refine regularly** — Review and cleanup periodically

---

## 🔗 Related Documents

- **[backlog.md](backlog.md)** — Prioritized work items (P-001 through P-014)
- **[plan.md](plan.md)** — Now/Next/Later roadmap
- **[status.md](status.md)** — Current state, risks, artifacts
- **[history.md](history.md)** — Major milestones timeline
- **[adr/](adr/)** — Architecture decision records
