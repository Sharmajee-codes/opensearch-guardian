# OpenSearch Guardian — Delivery Roadmap

## V0.1 → V1.0 Release Table

| Release | Scope | Write capability | Success criterion |
|---------|-------|------------------|-------------------|
| V0.1 | Electron shell, connection profiles, direct OpenSearch monitoring | None | Reliable live cluster overview |
| V0.2 | Doctor rules + evidence + CLI | None | Diagnoses fixture failures correctly |
| V0.3 | Cost optimizer + history | None | Actionable efficiency recommendations |
| V0.4 | Docker provisioning + capacity planner | Explicit approval | Add node and verify rebalance |
| V0.5 | Kubernetes Operator integration | Scoped RBAC + approval | Scale node pool and verify |
| V0.6 | MCP + optional LLM explanation | Read-only initially | External agents can query Guardian safely |
| V1.0 | Hardened cross-platform OSS release | Policy-controlled | Documented, tested, secure public release |

## Future Scope

- Multi-cluster/fleet operations and environment comparison.
- Predictive capacity planning based on ingestion, query load, retention, and growth.
- Historical incident timelines and automatic RCA generation.
- Safe remediation with policy engine, dry run, human approval, verification, and rollback.
- MCP server for Claude Code, Codex, Gemini and other agent clients.
- Pluggable AWS/Azure/GCP/self-hosted cost models.
- Helm and generic StatefulSet provisioning adapters.
- Remote storage/searchable snapshot/lifecycle optimization recommendations.
- OpenTelemetry correlation across logs, metrics, and traces.
- Alert integrations and incident-management integrations.
- Rule marketplace/community rule packs without making a hosted marketplace mandatory.
- Optional web/server mode for teams while retaining the standalone desktop/CLI experience.
- Simulation/digital-twin style capacity and rebalance impact estimation.
