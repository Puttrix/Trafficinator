# Open Questions

Track assumptions and unknowns. When answered, move to history or link ADR.

## Architecture & Design
- **Q1:** Should we add a control API, or keep it pure configuration-driven?
  - Current: Parked web UI, config via environment variables only
  - Tradeoff: Simplicity vs. ease of use

- **Q2:** Is the current token-bucket rate limiting optimal for all scenarios?
  - Current: Works well for steady traffic, may need burst mode

- **Q3:** Should we support distributed load generation (multiple containers)?
  - Use case: Very high volume loads (100k+/day)

## Features & Roadmap
- **Q4:** What's the right balance between realism and configurability?
  - Risk: Too many options = complexity, too few = limited use cases

- **Q5:** Should we add more sophisticated user journey modeling?
  - Example: Multi-step funnels, cart abandonment simulation

- **Q6:** Do users need traffic replay from actual logs?
  - Alternative: Generate from patterns vs. replay real logs

## Deployment & Operations
- **Q7:** Should we provide Kubernetes manifests alongside Docker Compose?
  - Community interest unclear

- **Q8:** Is Watchtower the right auto-update strategy?
  - Current: Works well for Portainer deployments

- **Q9:** Should we offer SaaS-style hosted load testing?
  - Revenue opportunity vs. maintenance burden

## Documentation & Community
- **Q10:** What information is missing for first-time users?
  - Feedback needed from new users

- **Q11:** Should we create video tutorials?
  - Text docs vs. video content investment 
