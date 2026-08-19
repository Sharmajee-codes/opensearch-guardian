# Component Contract — Module Boundaries & IPC

**Author:** Phyllis (T7)
**Date:** 2026-08-19
**Purpose:** Define authoritative module boundaries for the Guardian codebase and the IPC/API boundary between the Electron renderer and the Python core.

---

## 1. Architecture Layers

Per SOP §4, Guardian is layered as follows:

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1: Electron / React UI (Renderer Process)                 │
│   - Displays cluster state, diagnoses, recommendations           │
│   - Collects user input (connection profiles, approval choices)  │
│   - NEVER contains credentials or executes shell commands        │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼  IPC (restricted channel)
┌─────────────────────────────────────────────────────────────────┐
│ Layer 2: IPC / API Boundary                                     │
│   - Serializes/deserializes messages between renderer and core   │
│   - Enforces permission checks (read-only vs. write-enabled)     │
│   - Validates all input from renderer before passing to core     │
│   - Implements WebSocket/SSE push for real-time updates          │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│ Layer 3: Guardian Core Service (Python FastAPI)                 │
│   - Orchestrates all collector, diagnosis, and provisioning work │
│   - Manages the collection scheduler (tiered cadence)            │
│   - Exposes REST API for CLI and future web mode                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Module Boundaries

### 2.1 `guardian/connections/` — Connection Manager + Secret Store

**Responsibilities:**
- Manage connection profiles (OpenSearch URL, auth method, TLS config)
- Validate connection reachability and permissions on profile creation
- Store credentials in OS keychain (macOS Keychain, Windows Credential Manager, Linux libsecret)
- Track connection health and auto-reconnect with backoff
- Separate monitoring credentials from provisioning credentials within the same profile

**Public interface (internal to core):**
```python
class ConnectionProfile(BaseModel):
    name: str
    opensearch_url: HttpUrl
    auth_method: Literal["basic", "cert", "api_key", "custom"]
    tls_verify: bool = True
    tls_ca_path: Optional[str] = None
    permissions: Literal["monitoring", "full"] = "monitoring"
    # Credentials stored in OS keychain, NOT in this model
    credential_store_key: str

class ConnectionStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    ERROR = "error"
```

**Dependencies:** `guardian/models/`, `guardian/safety/` (for permission checks)

---

### 2.2 `guardian/collectors/` — OpenSearch Collector

**Responsibilities:**
- Implement the tiered collection strategy (SOP §4.2, ADR-005)
- Call OpenSearch REST APIs at appropriate cadences
- Normalize raw API responses into version-agnostic internal models
- Handle API errors, timeouts, and partial responses gracefully
- Support adaptive cadence during incidents (increase frequency of cheap signals)

**Public interface:**
```python
class CollectorConfig(BaseModel):
    cadence_health: timedelta = timedelta(seconds=5)
    cadence_metrics: timedelta = timedelta(seconds=12)
    cadence_storage: timedelta = timedelta(seconds=45)
    cadence_deep: timedelta = timedelta(minutes=5)
    adaptive_mode: bool = True

class CollectionResult(BaseModel):
    cluster_snapshot: Optional[ClusterSnapshot] = None
    node_snapshots: dict[str, NodeSnapshot] = field(default_factory=dict)
    index_snapshots: dict[str, IndexSnapshot] = field(default_factory=dict)
    cluster_settings: Optional[ClusterSettings] = None
    collected_at: datetime
    errors: list[str] = field(default_factory=list)
```

**Dependencies:** `guardian/models/`, `guardian/connections/`

---

### 2.3 `guardian/models/` — Normalized Internal Models

**Responsibilities:**
- Define all version-agnostic data models used across the system
- Serve as the contract between collectors, rules, optimizer, and provisioning
- Must be stable across OpenSearch 1.x and 2.x upgrades

**Key models (see `data-model.md` for full field definitions):**
- `ClusterSnapshot` — health, shard counts, node counts, timestamp
- `NodeSnapshot` — JVM, CPU, memory, disk, thread pool, roles
- `ShardState` — allocation state, shard size, recovery progress
- `IndexSnapshot` — doc count, store size, segment count, settings
- `ClusterSettings` — persistent and transient settings
- `Finding` — diagnostic finding with evidence and severity
- `Recommendation` — action recommendation with classification
- `ProvisioningPlan` — planned infrastructure change

---

### 2.4 `guardian/rules/` — Doctor Rules

**Responsibilities:**
- Contain all deterministic diagnostic rules
- Each rule has: rule ID, name, severity, entities it applies to, condition logic, evidence extraction, and remediation guidance
- Rules operate on normalized models from `guardian/models/`
- Rules are pure functions (no side effects, no network calls)

**Rule file format (YAML + Python evaluation):**
```yaml
rule_id: RULE-001
name: "Cluster health is red"
severity: critical
applies_to: cluster
condition: "snapshot.status == 'red'"
evidence:
  - "snapshot.unassigned_shards > 0"
  - "snapshot.relocating_shards > 0"
remediation: "Check unassigned shards via allocation explain API"
safety_level: information
```

**Dependencies:** `guardian/models/`

---

### 2.5 `guardian/diagnosis/` — Correlation Engine

**Responsibilities:**
- Run all rules against the latest snapshot(s)
- Correlate findings across rule families (e.g., disk watermark + unassigned shards → allocation cascade)
- Compute confidence and severity scores
- Produce the final `Finding` list for a given snapshot
- Track finding resolution across snapshots (never mark resolved without verification)

**Public interface:**
```python
class DiagnosisResult(BaseModel):
    findings: list[Finding]
    correlated_findings: list[CorrelatedFinding]
    snapshot_id: str
    analyzed_at: datetime
    unresolved_since: Optional[str] = None  # earlier snapshot ID
```

**Dependencies:** `guardian/models/`, `guardian/rules/`

---

### 2.6 `guardian/optimizer/` — Cost Optimizer

**Responsibilities:**
- Analyze index/storage statistics for efficiency opportunities
- Produce recommendations for retention, shard reduction, tiering, replica optimization
- Never claim exact currency savings; always show assumptions and confidence
- Operate on `IndexSnapshot` and `ClusterSnapshot` data

**Output classification:**
- `ReclaimableStorage` — old data, low-access indices, duplicate snapshots
- `ShardReduction` — tiny shards, oversharded indices, rollover opportunities
- `ReplicaOptimization` — unnecessary replica overhead
- `MappingOptimization` — high field count, unnecessary indexed fields
- `CapacityRecovery` — node utilization imbalance, rightsizing

**Dependencies:** `guardian/models/`, `guardian/rules/`

---

### 2.7 `guardian/capacity/` — Capacity Planner

**Responsibilities:**
- Project future resource needs based on current trends
- Support rightsizing recommendations
- Integrate with provisioning planning (SOP §7, step 3)

**Dependencies:** `guardian/models/`, `guardian/optimizer/`

---

### 2.8 `guardian/provisioning/` — Provisioning Engine

**Sub-modules:**
- `guardian/provisioning/docker/` — Docker Compose and Docker Engine API adapter
- `guardian/provisioning/kubernetes/` — Kubernetes API adapter (Operator-focused)

**Responsibilities:**
- Implement the 12-stage provisioning state machine (SOP §7, ADR-006)
- Enforce the approval gate (step 6) before any infrastructure mutation
- Record every mutation in the audit log
- Support dry-run/diff view
- Never create unmanaged pods beside an Operator-managed cluster
- Match version, cluster name, discovery, security, and storage settings

**State machine states:**
```python
class ProvisioningState(Enum):
    DISCOVER = "discover"
    SNAPSHOT = "snapshot"
    PLAN = "plan"
    PREFLIGHT = "preflight"
    REVIEW = "review"
    APPROVE = "approve"
    APPLY = "apply"
    OBSERVE = "observe"
    VERIFY_JOIN = "verify_join"
    REBALANCE = "rebalance"
    VALIDATE = "validate"
    AUDIT = "audit"
    ROLLBACK = "rollback"
    CANCELLED = "cancelled"
```

**Dependencies:** `guardian/models/`, `guardian/safety/`, `guardian/audit/`, `guardian/connections/`

---

### 2.9 `guardian/safety/` — Safety Engine

**Responsibilities:**
- Classify all recommendations: Informational, Safe/Reversible, Approval Required, Destructive
- Enforce V1 policy: no autonomous deletion of indices, PVCs, nodes, or snapshots
- Validate provisioning plans against safety rules before Apply stage
- Check that write access is explicitly enabled for a connection before allowing mutations
- Manage the dry-run mode for infrastructure changes

**Public interface:**
```python
class SafetyClassification(Enum):
    INFORMATIONAL = "informational"
    SAFE_REVERSIBLE = "safe_reversible"
    APPROVAL_REQUIRED = "approval_required"
    DESTRUCTIVE = "destructive"

def classify(action: str, context: dict) -> SafetyClassification
def validate_plan(plan: ProvisioningPlan, connection: ConnectionProfile) -> list[str]  # returns violations
```

**Dependencies:** `guardian/models/`, `guardian/connections/`

---

### 2.10 `guardian/audit/` — Audit + Verification Engine

**Responsibilities:**
- Log all write operations with who/what/when, requested change, actual change, result
- Retain before/after state for all provisioning actions
- Provide immutable audit trail (append-only, locally stored)
- Support post-incident review

**Dependencies:** `guardian/models/`, `guardian/provisioning/`

---

### 2.11 `guardian/llm/` — Optional LLM Explanation Layer

**Responsibilities:**
- Summarize and correlate established findings from the Doctor
- Generate human-readable explanations of complex diagnostic chains
- NEVER introduce new facts or override deterministic findings
- Clearly label LLM-generated content as "explanatory, not diagnostic"

**Public interface:**
```python
async def summarize_findings(findings: list[Finding], context: dict) -> str
async def explain_diagnosis(finding: Finding, evidence: dict) -> str
```

**Dependencies:** `guardian/models/`, `guardian/diagnosis/`

---

## 3. IPC / API Boundary

### 3.1 Electron ↔ Core Communication

The boundary between the Electron renderer and the Python core is a **restricted IPC channel**:

- **Message format:** JSON over a local Unix socket (macOS/Linux) or named pipe (Windows)
- **Direction:** Bidirectional, but the renderer can only initiate read operations; the core pushes updates via WebSocket/SSE
- **Permission enforcement:** The IPC layer checks the caller's permission level before routing to core modules
- **Credential isolation:** No credentials pass through the IPC layer; the core holds them in the keychain

### 3.2 IPC Message Types

| Direction | Message | Purpose |
|-----------|---------|---------|
| Renderer → Core | `connection.list` | Get list of connection profiles |
| Renderer → Core | `connection.add` | Create new connection profile (credentials stored separately) |
| Renderer → Core | `connection.test` | Test connectivity and permissions |
| Renderer → Core | `cluster.health` | Get current cluster health snapshot |
| Renderer → Core | `cluster.metrics` | Get detailed node/metric snapshots |
| Renderer → Core | `diagnosis.run` | Trigger a fresh diagnosis pass |
| Renderer → Core | `diagnosis.history` | Get historical findings |
| Renderer → Core | `optimizer.run` | Trigger cost analysis |
| Renderer → Core | `provisioning.plan` | Start a provisioning workflow |
| Renderer → Core | `provisioning.approve` | Submit approval for a provisioning step |
| Renderer → Core | `provisioning.rollback` | Initiate rollback |
| Core → Renderer | `snapshot.update` | Push updated cluster snapshot |
| Core → Renderer | `finding.new` | Push new diagnostic finding |
| Core → Renderer | `finding.resolved` | Push resolved finding |
| Core → Renderer | `provisioning.state` | Push provisioning state machine transition |

### 3.3 Security Constraints at the Boundary

1. **No shell execution** from the renderer process
2. **No credential transmission** — credentials stay in the OS keychain
3. **No arbitrary code execution** — all core operations go through the IPC layer
4. **Input validation** — all renderer messages are validated against schemas before reaching core modules
5. **Audit logging** — all IPC calls are logged with timestamps and caller identity

---

## 4. Module Dependency Graph

```
apps/desktop (Electron)
    │
    ▼ (IPC)
guardian/core (FastAPI entry point)
    │
    ├── guardian/connections/
    │       └── guardian/models/
    │
    ├── guardian/collectors/
    │       ├── guardian/models/
    │       └── guardian/connections/
    │
    ├── guardian/diagnosis/
    │       ├── guardian/models/
    │       └── guardian/rules/
    │
    ├── guardian/optimizer/
    │       └── guardian/models/
    │
    ├── guardian/capacity/
    │       ├── guardian/models/
    │       └── guardian/optimizer/
    │
    ├── guardian/provisioning/
    │       ├── guardian/provisioning/docker/
    │       ├── guardian/provisioning/kubernetes/
    │       ├── guardian/models/
    │       ├── guardian/safety/
    │       ├── guardian/audit/
    │       └── guardian/connections/
    │
    ├── guardian/safety/
    │       └── guardian/models/
    │
    ├── guardian/audit/
    │       └── guardian/models/
    │
    └── guardian/llm/
            └── guardian/models/
```

---

## 5. References

- SOP §4 — Proper Implementation Architecture
- SOP §4.1 — Suggested technology stack
- SOP §4.2 — Collection strategy
- ADR-001 (Primary Data Plane), ADR-003 (Technology Stack), ADR-006 (Provisioning State Machine)
- `docs/architecture/data-model.md` (sibling document)
