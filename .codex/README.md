# .codex — Project Memory

A lightweight, human-first memory of conversations, decisions, and rationale.

How to use
- Append new entries to `memory.md` (newest at the top).
- Use the template in `TEMPLATE.md` for consistent structure.
- Reference files with clickable paths (e.g., `README.md:472`).
- Keep sensitive tokens/URLs redacted.

What to capture
- Decisions and their why
- Open questions and next steps
- Links to relevant files/PRs/issues
- Gotchas, constraints, and context that will be forgotten later

Conventions
- One top-level `##` per entry with an ISO date and short title
- Short, scannable bullets; avoid walls of text
- Prefer facts over speculation; mark assumptions clearly

Scope
- Engineering/product discussions for Trafficinator and adjacent tooling (e.g., control UI)
- Non-binding ideas are welcome; clearly label them as ideas

Authority
- Treat `.codex/memory.md` and `README.md` as primary, up-to-date sources.
- Consider helper docs like `CLAUDE.md` advisory only; ignore outdated parts and migrate good bits here.
