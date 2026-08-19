# OpenSearch Guardian — Standard Operating Procedure

## Purpose and Product Definition

OpenSearch Guardian is proposed as a fully open-source desktop operations console for OpenSearch. Its purpose is to connect safely to existing OpenSearch clusters, provide continuous cluster monitoring, diagnose operational problems, identify observability cost and capacity opportunities, and—where the deployment environment permits—provision or scale OpenSearch nodes through Docker or Kubernetes.

The product should not be designed as a replacement for OpenSearch, Kubernetes controllers, Docker, or existing monitoring systems. Guardian is the intelligence, safety, orchestration, visualization, and verification layer above them.

---

## Current Requirements

- Electron-based cross-platform desktop UI for macOS, Windows, and Linux.
- Connect directly to an existing OpenSearch REST endpoint for monitoring and diagnosis.
- Optionally connect to Docker when the cluster is container-managed and node provisioning is required.
- Optionally connect to Kubernetes when the cluster is Kubernetes-managed; use Kubernetes-native reconciliation rather than creating unmanaged pods.
- Live cluster monitoring: health, nodes, JVM, CPU, memory, disk, shards, indexing/search activity, recoveries, thread-pool pressure, and important events.
- Cluster Doctor: deterministic, evidence-backed diagnosis with severity, confidence, cause, evidence, and recommended action.
- Observability Cost Optimizer: identify retention, storage, shard, replica, mapping/indexing, tiering, and capacity inefficiencies.
- Guided Add Node / Scale Node Pool workflow with preflight checks, approval, deployment tracking, rebalance monitoring, and before/after verification.
- Read-only by default. Write/provisioning privileges must be explicitly enabled per connection.
- No mandatory proprietary cloud service, paid API, telemetry collector, or hosted backend.

---

## Recommended Connectivity Model

Guardian should treat OpenSearch connectivity and infrastructure connectivity as separate capabilities. Every useful installation needs an OpenSearch connection; Docker or Kubernetes access is optional and should only be requested when Guardian needs to manage the infrastructure hosting the cluster.

### Connectivity Modes

| Mode | Use for | Required | Write access | Recommendation |
|------|---------|----------|--------------|----------------|
| Direct OpenSearch | Monitoring, Doctor, Optimizer | OpenSearch URL + auth/TLS | No for V1 | Default / preferred |
| Docker + OpenSearch | Local/self-hosted container clusters + provisioning | OpenSearch + Docker Engine | Only for provisioning | V1 provisioning target |
| Kubernetes + OpenSearch | K8s-managed clusters + scaling | OpenSearch + Kubernetes API | Scoped RBAC | V1.5 target |

### 3.1 Direct Connection to OpenSearch — Preferred Monitoring Path

For monitoring, diagnosis, and optimization, connect directly to the OpenSearch REST API over HTTPS. Do not route routine cluster telemetry through Docker or Kubernetes simply because OpenSearch happens to run there. OpenSearch is the authoritative source for cluster health, shard allocation, node statistics, index statistics, settings, and many diagnostic signals. The official Cluster Health API reports green/yellow/red status and shard allocation state, while Cluster Stats and Nodes Stats expose cluster, node, JVM, CPU, memory, filesystem, index, and shard metrics.

**Recommended connection profile:**

- Endpoint: `https://host:9200` (or load balancer/service endpoint)
- Authentication adapters: basic auth first; client certificates and pluggable auth later
- TLS verification enabled by default; custom CA import supported
- Credentials stored using the operating system credential/keychain service, never plaintext project configuration
- Connection test verifies version, cluster UUID/name, permissions, security/TLS state, and required monitoring APIs
- Start with a least-privilege monitoring role; request additional permissions only for an approved action

### 3.2 Docker-Managed Cluster

Docker integration is an infrastructure-management adapter, not the monitoring transport. Guardian should still monitor through OpenSearch. When provisioning is enabled, use the Docker Engine API or a well-defined Compose management layer to inspect the current deployment, validate the OpenSearch version/network/volumes/configuration, create or update the desired node definition, start it, and then verify cluster membership through OpenSearch.

The official OpenSearch Docker documentation supports multi-container clusters and Docker Compose. Guardian should preserve the user's existing deployment definition where possible and should never silently convert an externally managed Compose stack into a Guardian-owned stack.

**Key rules:**

- Detect whether Guardian owns the deployment definition or is observing an external deployment
- Never add a node using `discover.type=single-node` to a multi-node production cluster
- Match compatible OpenSearch version, cluster name, discovery/network settings, security configuration, and persistent storage
- Require persistent volumes for data nodes unless the user explicitly selects an ephemeral development profile
- Run preflight → provision → wait for process → verify node joins → monitor relocation/recovery → verify health
- Record every infrastructure mutation in an immutable local audit log

### 3.3 Kubernetes-Managed Cluster

For Kubernetes, Guardian should use the Kubernetes API and work with the cluster's existing deployment controller. Where the OpenSearch Kubernetes Operator manages the cluster, Guardian should patch the appropriate OpenSearch custom resource/node pool and let the Operator reconcile StatefulSets, Pods, Services, storage, and lifecycle. Guardian must not create unmanaged OpenSearch pods beside an Operator-managed cluster.

**Key rules:**

- Read kubeconfig/context or use in-cluster credentials only with user consent
- Discover namespace, OpenSearch custom resource, node pools, StatefulSets, PVCs, Services, storage classes, and pod state
- Use narrowly scoped RBAC; monitoring access and provisioning access should be separate
- Show the exact desired-state change before applying it
- Watch reconciliation and pod readiness, then switch verification back to the OpenSearch APIs
- Support Helm/StatefulSet-managed clusters later through separate adapters; do not pretend every K8s cluster is Operator-managed

---

## Proper Implementation Architecture

The Electron renderer should never contain cluster administrator credentials or execute arbitrary shell commands. Use a layered architecture with a restricted IPC boundary and a backend/core service responsible for OpenSearch, Docker, Kubernetes, analysis, persistence, and privileged operations.

### Architecture Layers

1. Electron/React UI
2. Restricted IPC/API boundary
3. Guardian Core service
4. Connection Manager + Secret Store
5. OpenSearch Collector
6. Snapshot/History Store
7. Doctor Rules + Correlation Engine
8. Cost Optimizer + Capacity Planner
9. Provisioning/Safety Engine
10. Docker Adapter / Kubernetes Adapter
11. Audit + Verification Engine

### 4.1 Suggested Technology Stack

| Layer | Recommended technology | Reason |
|-------|------------------------|--------|
| Desktop | Electron + React + TypeScript | Cross-platform operator console |
| Core/API | Python 3.12+ + FastAPI + Pydantic | Strong infrastructure/data ecosystem |
| OpenSearch | opensearch-py + REST adapters | Official-style Python integration |
| CLI | Typer + Rich | Headless/server workflows and automation |
| Local persistence | SQLite | Zero-setup history/config metadata |
| Production history | PostgreSQL (optional) | Multi-user/server mode later |
| Streaming UI | WebSocket or SSE | Push normalized snapshots/events to Electron |
| Container integration | Docker Engine API | Avoid fragile shell parsing |
| Kubernetes | Official Kubernetes client | Native resource/RBAC/watch support |

### 4.2 Collection Strategy

Collectors should normalize API responses into stable internal models so that rules are not tightly coupled to a single OpenSearch version. Poll cheap signals frequently and expensive diagnostics less often. Use adaptive polling during incidents.

| Frequency | What to collect |
|-----------|-----------------|
| ~5 s | Cluster health / lightweight status |
| ~10–15 s | Selected node metrics and shard state |
| ~30–60 s | Index/storage statistics and recoveries |
| ~5 min | Expensive diagnostic/cost analyses, mappings, policies, and deeper scans |
| On-demand | Allocation explain, targeted index/node diagnostics, pre/post provisioning verification |

---

## Cluster Doctor Implementation

Diagnosis must be evidence-first and deterministic. LLMs may summarize, correlate, or explain established findings, but must not be the source of truth for health status, thresholds, or whether an action is safe.

### Processing Pipeline

```
OpenSearch APIs → normalized facts → deterministic rules → correlated findings → confidence/severity → recommendation → optional AI explanation
```

**Initial rule families:**

- Red/yellow health
- Unassigned shards
- Allocation failures
- Disk watermarks
- JVM pressure
- CPU saturation
- Excessive shard density
- Recovery pressure
- Thread-pool rejections
- Node loss
- Mapping explosion
- Oversized/tiny shards
- Stuck lifecycle policies
- Configuration risks

**Each finding contains:** rule ID, entity, observed value, threshold/context, severity, evidence, confidence, remediation guidance, and required safety level.

Never mark an issue resolved until a subsequent snapshot verifies the expected improvement.

---

## Observability Cost Optimizer Implementation

The optimizer should begin with resource efficiency rather than attempting universal currency estimates. Its first-class outputs are reclaimable storage, shard reduction, replica/storage opportunities, retention opportunities, unused indexing/mapping overhead, and potential capacity recovery. Cloud-specific price adapters can be added later.

**Analysis areas:**

- **Retention analysis:** age/size/access patterns versus current retention/lifecycle
- **Oversharding:** tiny shards, excessive shard count, rollover opportunities
- **Storage:** old/low-access data, tiering/remote-storage candidates, snapshots
- **Replica analysis:** availability requirements versus storage/compute overhead
- **Mappings:** high field count and potentially unnecessary indexed fields
- **Capacity:** node utilization imbalance and rightsizing opportunities

Every recommendation must show assumptions and confidence; never claim exact savings when the data is insufficient.

---

## Node Provisioning and Scaling SOP

| Step | Stage | Required behavior |
|------|-------|-------------------|
| 1 | Discover | Identify deployment type and authoritative manager: Docker/Compose, OpenSearch Operator, Helm/StatefulSet, or external. |
| 2 | Snapshot | Capture cluster health, nodes, shards, disk, JVM, versions, settings, and deployment metadata. |
| 3 | Plan | Calculate requested/Guardian-recommended role, count, CPU, memory, heap, storage, version, and expected impact. |
| 4 | Preflight | Validate credentials, permissions, version compatibility, network/discovery, storage, capacity, security material, and dependencies. |
| 5 | Review | Display exact desired-state change, risks, estimated rebalance impact, and rollback/recovery approach. |
| 6 | Approve | Require explicit approval for infrastructure writes. |
| 7 | Apply | Modify the authoritative deployment manager only. |
| 8 | Observe | Track container/pod startup and controller reconciliation. |
| 9 | Verify join | Confirm the new node appears through OpenSearch and has the expected roles/version. |
| 10 | Rebalance | Monitor initializing/relocating/unassigned shards and recovery pressure. |
| 11 | Validate | Compare before/after health, disk distribution, shard density, JVM/CPU pressure, and failures. |
| 12 | Audit | Persist who/what/when, requested change, actual change, result, and verification evidence. |

---

## Security and Safety Requirements

- Read-only is the default connection mode.
- Separate monitoring permissions from provisioning/remediation permissions.
- Store secrets in OS keychain/credential vault; redact them from logs, crash reports, exports, and diagnostics.
- TLS certificate validation is enabled by default.
- No arbitrary command execution from the renderer.
- Use explicit allow-listed operations for Docker/Kubernetes/OpenSearch mutations.
- Classify recommendations: Informational, Safe/Reversible, Approval Required, Destructive.
- V1 must not autonomously delete indices, PVCs, nodes, snapshots, or other data-bearing resources.
- Provide a dry-run/diff view for infrastructure changes.
- Audit all write operations and retain before/after state.

---

## Open-Source Strategy

Guardian should be useful without any proprietary backend. A contributor must be able to clone the repository, build the desktop app/core service, connect to a local OpenSearch cluster, and use the core Doctor/Optimizer without purchasing a service.

- **License:** Apache License 2.0 is a strong default candidate because OpenSearch itself is Apache-2.0 licensed, but the project should perform a dependency/license review before release. The Guardian repository should contain its own LICENSE and NOTICE where required and must respect OpenSearch trademark rules; being compatible with OpenSearch does not make Guardian an official OpenSearch project.
- **Repository:** Public GitHub repository with issues, discussions, milestones, and transparent roadmap.
- **Documentation:** LICENSE, NOTICE as applicable, CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md, SUPPORT.md, GOVERNANCE.md, and architecture decision records.
- **Developer environment:** Using Docker Compose with reproducible healthy/broken OpenSearch fixtures.
- **Telemetry:** No mandatory telemetry. If optional anonymous telemetry is ever added, make it opt-in and document the schema.
- **Plugin interfaces:** For authentication, LLMs, cost models, Docker/K8s provisioners, exporters, and diagnostic rules.
- **Release integrity:** Signed releases, checksums, SBOM, dependency scanning, secret scanning, reproducible build guidance, and responsible disclosure process.
- **Transparency:** Public rule definitions and test fixtures so operators can audit why Guardian made a diagnosis.

---

## Suggested Repository Structure

```
opensearch-guardian/
├── apps/
│   ├── desktop/          # Electron + React
│   ├── api/              # Guardian API/core service entry point
│   └── cli/              # Headless CLI
├── guardian/
│   ├── connections/
│   ├── collectors/
│   ├── models/
│   ├── rules/
│   ├── diagnosis/
│   ├── optimizer/
│   ├── capacity/
│   ├── provisioning/
│   │   ├── docker/
│   │   └── kubernetes/
│   ├── safety/
│   ├── audit/
│   └── llm/              # Optional explanation/provider layer
├── rules/
├── fixtures/
├── tests/
├── docs/
│   ├── architecture/
│   ├── operations/
│   └── adr/
├── deploy/
│   ├── docker/
│   └── kubernetes/
├── LICENSE
├── CONTRIBUTING.md
├── SECURITY.md
└── README.md
```

---

## Delivery Roadmap

See [roadmap.md](operations/roadmap.md).

---

## Future Scope

See [roadmap.md](operations/roadmap.md).

---

## Acceptance Criteria for the First Public MVP

See [acceptance-criteria.md](operations/acceptance-criteria.md).

---

## Key Architectural Decision

Direct OpenSearch connectivity is the primary data plane. Docker and Kubernetes are optional control-plane adapters used only when infrastructure management is requested. This separation keeps Guardian useful for bare-metal, VM, managed, Docker, and Kubernetes clusters; reduces privileges; and prevents the desktop application from becoming coupled to one deployment model.

---

## References

1. OpenSearch Documentation — Cluster Health API: https://docs.opensearch.org/latest/opensearch/rest-api/cluster-health/
2. OpenSearch Documentation — Cluster Stats API: https://docs.opensearch.org/latest/api-reference/cluster-api/cluster-stats/
3. OpenSearch Documentation — Nodes Stats API: https://docs.opensearch.org/latest/api-reference/nodes-apis/nodes-stats/
4. OpenSearch Documentation — Docker: https://docs.opensearch.org/latest/install-and-configure/install-opensearch/docker/
5. OpenSearch Project GitHub — OpenSearch (Apache License 2.0): https://github.com/opensearch-project/OpenSearch
