# Backlog

## Documentation & Alignment
- [ ] **P-001** Update CLAUDE.md to reference correct docker-compose files
      tags: documentation, maintenance  priority: medium  est: 1h
      deps: none
      accepts: CLAUDE.md references docker-compose.yml and docker-compose.prod.yml instead of docker-compose.loadgen.yml; notes URLs are embedded in image

- [ ] **P-002** Update CLAUDE.md to reflect embedded URLs vs config/urls.txt
      tags: documentation, maintenance  priority: medium  est: 0.5h
      deps: P-001
      accepts: Documentation clearly states URLs are built into Docker image

## Testing & Quality
- [ ] **P-003** Enhance test coverage for complex behaviors
      tags: testing, quality  priority: high  est: 4h
      deps: none
      accepts: Tests cover events, ecommerce, daily cap, and action ordering guarantees

- [ ] **P-004** Add validation utilities for configuration
      tags: testing, devx  priority: medium  est: 3h
      deps: none
      accepts: Script validates env vars and tests Matomo connectivity before load test

## Features - Short Term
- [ ] **P-005** Create load preset configurations (Light/Medium/Heavy)
      tags: feature, usability  priority: low  est: 2h
      deps: none
      accepts: Example compose files or env templates for Light (1k/day), Medium (10k/day), Heavy (50k+/day)

- [ ] **P-006** Improve realistic traffic patterns with user journeys
      tags: feature, realism  priority: medium  est: 6h
      deps: none
      accepts: Define and implement user journey templates (researcher, buyer, casual browser)

## Features - Mid/Long Term
- [ ] **P-007** Evaluate Control UI/API feasibility
      tags: feature, webui, parked  priority: low  est: 16h
      deps: none
      accepts: Technical feasibility study with pros/cons; see .codex/webui-parked.md

- [ ] **P-008** Multi-target support (test multiple Matomo instances)
      tags: feature, scaling  priority: low  est: 8h
      deps: none
      accepts: Config supports multiple MATOMO_URL entries with independent visit targets

- [ ] **P-009** Advanced reporting about load generation itself
      tags: feature, observability  priority: low  est: 6h
      deps: none
      accepts: Metrics endpoint or log output showing actual visits/day, success rate, latency

- [ ] **P-010** Plugin/extension system for custom traffic patterns
      tags: feature, extensibility  priority: low  est: 12h
      deps: none
      accepts: Users can add Python modules to define custom traffic behaviors

## Infrastructure
- [ ] **P-011** Kubernetes manifests for k8s deployments
      tags: infra, k8s  priority: low  est: 4h
      deps: none
      accepts: Helm chart or plain manifests for deploying Trafficinator in k8s

- [ ] **P-012** Distributed load generation (multiple containers)
      tags: infra, scaling  priority: low  est: 8h
      deps: none
      accepts: Coordinate multiple containers to generate 100k+/day loads

## Community & Documentation
- [ ] **P-013** Video tutorials for common scenarios
      tags: documentation, community  priority: low  est: 6h
      deps: none
      accepts: YouTube videos covering setup, configuration, and troubleshooting

- [ ] **P-014** Gather community feedback on feature priorities
      tags: community, planning  priority: medium  est: 2h
      deps: none
      accepts: GitHub discussion or survey to understand user needs
