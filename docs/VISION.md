# OpenSearch Guardian — Product Vision

## What It Is

OpenSearch Guardian is a fully open-source desktop operations console that provides continuous cluster monitoring, AI-assisted diagnosis, cost optimization, and safe provisioning capabilities for OpenSearch deployments. It connects directly to existing OpenSearch clusters to deliver real-time insights without requiring proprietary backends or hosted services.

## Why It Exists

Operations teams managing OpenSearch clusters face three critical challenges:
1. **Visibility Gap**: Native OpenSearch tools lack unified monitoring, diagnosis, and optimization in a single interface
2. **Risk Exposure**: Manual provisioning and ad-hoc changes can destabilize production clusters
3. **Vendor Lock-in**: Many solutions require proprietary cloud services or paid telemetry collectors

Guardian bridges this gap by offering a safe, transparent, and vendor-neutral alternative that puts cluster intelligence directly in operators' hands.

## Who It Serves

- **Site Reliability Engineers (SREs)** who need rapid diagnosis of cluster issues with evidence-backed remediation
- **DevOps Engineers** managing OpenSearch deployments who require safe provisioning workflows
- **Platform Teams** operating multi-tenant OpenSearch environments seeking cost optimization insights
- **OpenSearch Administrators** wanting vendor-independent monitoring and diagnostic capabilities

## Core Value Propositions

### Continuous Monitoring
Real-time cluster health, node performance, shard allocation, and indexing/search activity visualized through an intuitive desktop interface. Guardian treats OpenSearch REST API as the authoritative data source for all monitoring functions.

### Cluster Doctor
Deterministic, evidence-first diagnosis engine that identifies issues with severity ratings, confidence levels, root cause analysis, and specific remediation guidance. Every finding is backed by verifiable evidence from cluster APIs.

### Observability Cost Optimizer
Identifies reclaimable storage, oversharding opportunities, inefficient retention policies, and mapping/indexing inefficiencies without requiring currency conversion or proprietary pricing models.

### Safe Provisioning & Scaling
When infrastructure access is available, Guardian enables controlled node addition/scaling through Docker or Kubernetes with explicit user approval, preflight validation, and immutable audit trails.

## What It Is NOT

Guardian deliberately avoids:
- Replacing OpenSearch itself (it monitors and optimizes existing clusters)
- Acting as a Kubernetes controller or Docker orchestration platform
- Requiring proprietary cloud services, paid APIs, or mandatory telemetry collectors
- Serving as a general-purpose observability platform (focused exclusively on OpenSearch)

## Positioning vs Alternatives

| Feature | OpenSearch Dashboards | Bolt-on Dashboards | OpenSearch Guardian |
|---------|----------------------|-------------------|---------------------|
| Deployment Model | Bundled with OpenSearch | Varied | Standalone Desktop |
| Primary Focus | Visualization | General Analytics | Monitoring + Doctor + Optimizer + Provisioning |
| Provisioning | Limited | Usually absent | Safe, gated workflows |
| Doctor Capabilities | Basic | Varies by implementation | Evidence-first, deterministic |
| Cost Optimization | Limited | Rare | First-class, assumption-transparent |
| Infrastructure Agnostic | OpenSearch-only | Vendor-specific | Bare-metal, VM, Docker, K8s |
| Open Source | Yes | Often no | Yes (Apache-2.0) |
| Backend Dependency | None | Often proprietary | Zero mandatory backend |

## Guiding Principles

### Read-Only by Default
All connections start in read-only mode. Infrastructure write/provisioning privileges require explicit per-connection approval, reducing accident risk and aligning with least-privilege security principles.

### Evidence-First Diagnosis
Diagnostic rules produce findings with verifiable evidence from cluster APIs. LLMs may explain findings but never determine health status or safety of actions.

### Infrastructure Agnostic
Treats OpenSearch connectivity as the primary data plane. Docker and Kubernetes are optional control-plane adapters activated only when provisioning is requested, keeping the core monitoring stack decoupled from deployment topology.

### Transparent Governance
Fully auditable diagnostic rules, public plugin interfaces, signed releases with SBOM, and transparent roadmap driven by community input rather than opaque telemetry.

## Non-Goals

- Replacing OpenSearch's native REST API or query capabilities
- Providing log aggregation or tracing collection (focus remains on metrics and cluster state)
- Offering multi-cluster federation in V0.1-V0.2 (single-cluster focus first)
- Acting as a general configuration management platform for non-OpenSearch infrastructure

## Success Signals

### V0.1-V0.2 Focus
- Reliable live cluster overview through direct OpenSearch connection
- Correct diagnosis of common cluster issues (red/yellow health, unassigned shards, disk watermarks, etc.)
- Actionable cost optimization recommendations with clear assumptions
- Safe Docker provisioning workflow with explicit approval and verification
- Kubernetes Operator integration with scoped RBAC and StatefulSet reconciliation

### Longer-Term
- Multi-cluster fleet operations with environment comparison
- Predictive capacity planning based on ingestion and query patterns
- Historical incident timelines with automated root cause analysis
- Safe remediation workflows with policy engines and verification
- OpenTelemetry correlation across logs, metrics, and traces
- Rule marketplace for community-contributed diagnostic rules

## Core Functionality Overview

Upon launch, Guardian presents:
1. **Cluster Explorer** - Add and manage OpenSearch connections with TLS/auth configuration
2. **Live Dashboard** - Real-time health, performance, and resource utilization panels
3. **Doctor View** - Active findings with evidence, severity, and remediation guidance
4. **Optimizer Tab** - Cost/saving opportunities with assumptions clearly stated
5. **Provisioning Wizard** - (When enabled) Guided node addition/scaling with preflight checks
6. **Audit Log** - Immutable record of all infrastructure changes and verification evidence

All core functionality operates without mandatory backend services, proprietary APIs, or paid subscriptions—requiring only access to an OpenSearch cluster and (optionally) Docker/Kubernetes when provisioning is desired.