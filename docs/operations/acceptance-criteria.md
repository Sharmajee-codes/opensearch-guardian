# OpenSearch Guardian — Acceptance Criteria for the First Public MVP

- [ ] Connect securely to a supported OpenSearch cluster using a least-privilege profile.
- [ ] Display live health and node/shard/resource information without requiring Docker or Kubernetes access.
- [ ] Survive unavailable nodes/API failures without freezing the Electron UI.
- [ ] Run deterministic Doctor rules and show evidence for every finding.
- [ ] Produce cost/capacity recommendations with assumptions and no fabricated savings.
- [ ] Persist local history and audit data without storing plaintext secrets.
- [ ] Docker provisioning is optional and cannot be invoked without explicit infrastructure access and approval.
- [ ] All core functionality works without a proprietary cloud service or paid LLM.
- [ ] Unit, integration, fixture, and end-to-end tests cover critical diagnostic and provisioning flows.
- [ ] Project can be built and run from the public repository using documented steps.
