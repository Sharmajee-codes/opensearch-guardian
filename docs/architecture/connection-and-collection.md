# Connection Manager & Collector Architecture

**Status:** Draft  
**Task:** T8 (R-CORE)  
**Author:** kelly-msyilpds  
**Reviewer:** phyllis-msyilmgq  
**Date:** 2026-08-19  
**Depends on:** T7 (phyllis — data-model.md, component-contract.md) — NOT YET PRESENT; design proceeds with assumptions noted below

---

## 1. Scope & Intent

This document designs the **Connection Manager** and **Collector** layers of the Guardian Core (Python/FastAPI service). It is a design-only artifact — no implementation code. The design governs how Guardian establishes, authenticates, validates, and maintains connections to OpenSearch clusters, and how it collects, normalizes, and dispatches cluster telemetry through a tiered adaptive cadence.

### Non-goals
- Docker/Kubernetes connection management (covered by T10/T11)
- Electron IPC boundary design (covered by T9)
- Provisioning state machine (covered by ADR-006 and T18/T20)
- LLM integration (covered by T16 domain)

### Key Constraints (from ADRs & SOP)
- **ADR-001**: Direct OpenSearch REST API is the primary data plane; no routing through infrastructure adapters for monitoring.
- **ADR-002**: Every connection starts read-only. Write/provisioning mode is explicitly enabled per-connection.
- **ADR-003**: Python 3.12+ / FastAPI / opensearch-py / Pydantic.
- **ADR-004**: Collector outputs normalized internal models consumed by deterministic rules — never raw API responses.
- **ADR-005**: Tiered adaptive cadence (5s / 10-15s / 30-60s / 5min / on-demand).
- **SOP §8**: Secrets in OS keychain only; TLS verify-on; read-only default; least-privilege roles.

---

## 2. Out-of-Order Dependency: Phyllis's Architecture Docs

The task instructs consuming `docs/architecture/data-model.md` and `component-contract.md` from T7. As of this writing (2026-08-19), **neither file exists** in the repository. T7 is still IN PROGRESS.

**Design assumption:** The normalized internal models will live in `guardian/models/` as Pydantic v2 classes. This document defines the shape and lifecycle of those models at the connection/collector boundary. Phyllis's data-model and component-contract will refine the internal type definitions; this document is written to be compatible with a clean model layer and will be updated when T7 lands.

**Risk:** If the model layer changes significantly (field renames, new model types, different granularity), the collector normalization contracts will need rebalancing. Mitigation: keep normalization logic in a thin adapter layer between raw opensearch-py responses and the model layer, making field-level changes localizable.

---

## 3. Connection Manager

### 3.1 Overview

The Connection Manager (`guardian/connections/`) is responsible for:
1. Storing connection profiles (endpoint, auth method, credentials reference, mode flags).
2. Resolving credentials from the OS keychain at connection time.
3. Establishing and validating the OpenSearch connection (version, cluster identity, permissions, TLS).
4. Maintaining a live client instance per active connection.
5. Gating write/provisioning operations behind per-connection enablement.
6. Detecting connection failures and driving reconnection.

### 3.2 Connection Profile Model

A connection profile is a persistent record describing one OpenSearch cluster. It is stored in SQLite (`connections` table) with credential references in the OS keychain.

```
ConnectionProfile
├── id: UUID (primary key)
├── name: str (human-readable label)
├── endpoint: str (HTTPS URL, e.g. https://search.example.com:9200)
├── auth_adapter: AuthAdapter (enum: basic, client_cert, custom_ca, none)
├── credential_ref: str (keychain key identifier, never the secret itself)
├── custom_ca_ref: str | null (keychain key for custom CA certificate)
├── tls_verify: bool (default: true; can be overridden for air-gapped dev clusters)
├── write_enabled: bool (default: false — ADR-002)
├── provisioning_enabled: bool (default: false — ADR-002)
├── mode: ConnectionMode (read_only | read_write | provisioning)
├── created_at: datetime
├── updated_at: datetime
├── last_test_result: ConnectionTestResult | null
├── last_test_at: datetime | null
├── is_active: bool (soft delete / toggle)
└── metadata: dict (arbitrary key-value for UI/extension use)
```

### 3.3 Auth Adapters

Auth adapters abstract the mechanics of authenticating to OpenSearch. Each adapter implements a common protocol.

#### AuthAdapter Protocol
```
interface AuthAdapter {
  resolve_credentials(ref: str) -> Credentials   # reads from keychain, never caches plaintext
  build_client_options() -> dict                 # returns kwargs for opensearch-py client
  validate(credentials: Credentials) -> bool     # fast login check
}
```

#### Built-in Adapters

| Adapter | Description | Priority |
|---------|-------------|----------|
| `BasicAuthAdapter` | Username/password from keychain. Default for V1. | Required |
| `ClientCertAuthAdapter` | mTLS with client certificate + key from keychain. | V1.1 |
| `CustomCAAuthAdapter` | Standard auth + custom CA bundle from keychain for self-signed clusters. | V1.1 |
| `NoAuthAdapter` | No auth (development only; disabled by default in production). | Dev-only |

**Keychain integration:**
- All secrets (passwords, client certs, private keys, CA bundles) are stored via `keyring` Python package, which delegates to the OS keychain (macOS Keychain, Windows Credential Manager, Linux Secret Service).
- The `credential_ref` is the keychain service name + account identifier.
- Secrets are **never** cached in memory beyond the lifetime of the HTTP client session. Each new connection or reconnection re-resolves from keychain.
- Logs, crash reports, exports, and diagnostics redact all credential fields. The keychain reference string is logged, not the secret.

### 3.4 Connection Test

Before a connection is marked active, the Connection Manager performs a **connection test** that validates five dimensions:

| Test | Method | What It Verifies |
|------|--------|------------------|
| **Version** | `GET /` | OpenSearch version string; compatibility check against known versions |
| **Cluster identity** | `GET /_cluster/health` | Cluster UUID and name; confirms single-cluster binding |
| **Permissions** | `GET /_nodes/stats`, `GET /_cluster/state`, `GET /*` (index list) | Read permissions for monitoring APIs; flags if write APIs are accessible (for audit) |
| **TLS** | SSL handshake verification | Certificate chain validity, expiry, hostname match |
| **Security state** | `GET /_security/authinfo` (if security plugin present) | Whether security is enabled; what roles the current user holds |

**Test result shape:**
```
ConnectionTestResult
├── passed: bool
├── version: str | null
├── cluster_uuid: str | null
├── cluster_name: str | null
├── read_permitted: bool
├── write_permitted: bool          # only true if connection has write scope
├── tls_valid: bool
├── tls_expiry: datetime | null
├── security_enabled: bool
├── user_roles: list[str]
├── errors: list[str]              # non-fatal warnings
├── fatal_errors: list[str]        # connection-test failure reasons
└── tested_at: datetime
```

**Pass criteria:** `passed=true` requires version resolved, cluster identity obtained, read permissions confirmed, and TLS valid. A connection with `write_permitted=true` but `write_enabled=false` on the profile is acceptable — the UI will surface that write access is available but currently disabled.

### 3.5 Write / Provisioning Mode Enablement

Per ADR-002, every connection starts in read-only mode. The path to enabling write or provisioning mode:

```
Profile created (write_enabled=false, provisioning_enabled=false)
  │
  ├─► UI shows "Read-only" badge
  │
  ├─► User clicks "Enable Write Access"
  │     │
  │     ├─► System prompts for confirmation (explicit consent)
  │     ├─► Connection test re-runs to verify write permissions exist
  │     ├─► If write_permitted=true in test:
  │     │     ├─► Profile updated: write_enabled=true
  │     │     └─► Audit log entry: who, when, what connection
  │     └─► If write_permitted=false:
  │           └─► Error: "Connection does not have write permissions. Update the OpenSearch role."
  │
  └─► User clicks "Enable Provisioning"
        │
        ├─► Same flow as write, plus provisioning_enabled=true
        └─► Additional check: user must have cluster admin or equivalent role
```

**Important:** Enabling write or provisioning on the profile does **not** grant additional OpenSearch permissions — it only flips a local flag. The actual permission check happens at the OpenSearch layer during each operation. The connection test's `write_permitted` field is a proxy; the authoritative check is the operation's response.

**Role guidance for least-privilege monitoring:**
The Connection Manager should provide operators with a recommended OpenSearch role definition for read-only monitoring. This role should include only:
- `view_index_metadata`
- `cluster:monitor/main`
- `cluster:monitor/health`
- `cluster:monitor/state`
- `cluster:monitor/node/stats`
- `indices:monitor/settings/get`
- `indices:monitor/stats`
- `indices:monitor/list`

Full role definition to be documented in a companion reference; the app UI can surface a copyable JSON role template.

### 3.6 Active Connection Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                     Connection Lifecycle                         │
│                                                                  │
│  CREATED ──► TESTING ──► ACTIVE ──► FAILED ──► RECOVERING     │
│     ▲                                         │       │         │
│     │                                         │       └──► ACTIVE  │
│     └─────────────────────────────────────────┘                │
│                                                              │
│  DELETED (soft)                                               │
└─────────────────────────────────────────────────────────────────┘
```

| State | Description |
|-------|-------------|
| `CREATED` | Profile saved; connection test not yet run or pending. |
| `TESTING` | Connection test in progress. UI shows spinner. |
| `ACTIVE` | Test passed; client instance live; collectors attached. |
| `FAILED` | Test or health check failed. UI shows error; user can retry. |
| `RECOVERING` | Automatic reconnection attempt in progress (exponential backoff). |

**Reconnection strategy:**
- On connection failure, enter `RECOVERING` state.
- Retry with exponential backoff: 2s, 4s, 8s, 16s, 32s (cap at 32s).
- On successful reconnect, return to `ACTIVE`.
- On persistent failure (e.g., 10 consecutive failures), transition to `FAILED` and notify the user.
- Collectors pause automatically when the connection is not `ACTIVE`.

---

## 4. Collector Architecture

### 4.1 Overview

The Collector (`guardian/collectors/`) is responsible for polling OpenSearch APIs at the cadence defined by ADR-005, normalizing raw API responses into version-agnostic internal models, and making those models available to downstream consumers (Doctor rules, cost optimizer, UI via SSE/WebSocket).

### 4.2 Tiered Collection Cadence

| Tier | Interval | APIs Polled | Purpose | Normalized Output |
|------|----------|-------------|---------|-------------------|
| **T1 — Live** | ~5s | `/_cluster/health`, `/_cat/nodes?h=name,heapPercent,jvm.percent,cpu`, `/_cat/thread_pool?h=name,active,queue,rejected` | Live UI overview, alert triggering | `ClusterHealthSnapshot`, `NodeStatusSnapshot` |
| **T2 — Trending** | ~10-15s | `/_nodes/stats`, `/_cat/shards`, `/_cat/recovery`, thread pool details | Trending, Doctor rule evaluation | `NodeStatsSnapshot`, `ShardStateSnapshot` |
| **T3 — Deep** | ~30-60s | `/_stats`, `/_cluster/settings`, `/_cat/indices`, index-level recoveries | Cost optimizer, capacity planner | `IndexStatsSnapshot`, `ClusterSettingsSnapshot` |
| **T4 — Diagnostic** | ~5min | Mapping scans, ILM policies, allocation explain (sampled), segment stats | Proactive optimization recommendations | `MappingSnapshot`, `ILMPolicySnapshot`, `AllocationSnapshot` |
| **T5 — On-demand** | User-triggered | Any targeted API | User-initiated deep dives | Per-request normalized response |

### 4.3 Collector Orchestrator

The orchestrator (`CollectorOrchestrator`) manages the lifecycle of all tier collectors for a given connection.

```
CollectorOrchestrator (per active connection)
├── tiers: dict[Tier, Collector]
├── state: CollectorState (idle | running | paused | errored)
├── incident_mode: bool         # adaptive: increase T1/T2 frequency
├── last_polled: dict[Tier, datetime]
├── errors: list[CollectionError]
└── hooks:
    ├── on_snapshot(tier, snapshot) -> None   # push to shared snapshot store
    ├── on_error(tier, error) -> None         # log and surface to UI
    └── on_incident_changed(active: bool) -> None  # adaptive mode trigger
```

**Scheduler:** Uses `asyncio` tasks with `asyncio.sleep()` for each tier. A master coordinator task manages the loop, handles backpressure, and enforces minimum inter-request delays to avoid overwhelming the cluster.

### 4.4 Adaptive Polling During Incidents

When an incident is detected (e.g., cluster health transitions to red or yellow, shard allocation failures spike), the collector enters **adaptive mode**:

| Condition | Action |
|-----------|--------|
| Health → red | T1 cadence: 5s → 2s; T2 cadence: 15s → 5s; T3-T4 paused |
| Health → yellow | T1 cadence: 5s → 3s; T2 cadence: 15s → 10s; T3 continues |
| Health → green (recovered) | Return to normal cadence after 60s of stability |
| Shard allocation failure detected | T2 cadence: 15s → 5s; T4: sample allocation-explain every 5min → every 30s |
| Recovery in progress | T2 cadence: 15s → 10s until recovery completes |
| Incident cleared | Return to normal cadence after stability window |

Adaptive mode is **stateful** — it tracks the current mode and transitions are driven by observable signals from the normalized data, not heuristics. The incident signal source is the Doctor rule engine (cross-cutting; T16 owns rule definitions, but T14 owns the adaptive trigger contract).

### 4.5 Normalization Layer

Each tier collector implements a **normalizer** — a function that takes a raw opensearch-py API response and produces one or more Pydantic model instances.

```python
# Contract (design, not implementation)
class Normalizer:
    def normalize(self, raw_response: dict, connection_version: str) -> NormalizedSnapshot:
        """Transform raw OpenSearch API response to version-agnostic model."""
        ...
```

**Normalization principles:**
1. **Version tolerance:** Handle field name changes across OpenSearch versions (e.g., `jvm.mem.heap_used_percent` vs. `jvm.mem.heap_pct`). Use version-aware field resolution.
2. **Lossless where possible:** Preserve raw values alongside normalized fields for debugging.
3. **Null-safety:** Missing fields become `None`, not exceptions. Document which fields are required vs. optional.
4. **Type coercion:** Convert string timestamps to `datetime`, string numbers to typed numbers, etc.
5. **Aggregation:** Some raw responses contain per-node/per-index arrays; normalizers may flatten or summarize as appropriate for the tier.

**Normalization output example (T1 — Cluster Health):**

Raw `GET /_cluster/health`:
```json
{
  "cluster_name": "prod-cluster",
  "status": "yellow",
  "timed_out": false,
  "number_of_nodes": 5,
  "number_of_data_nodes": 3,
  "active_primary_shards": 50,
  "active_shards": 100,
  "relocating_shards": 0,
  "initializing_shards": 2,
  "unassigned_shards": 5,
  "delayed_unassigned_shards": 0,
  "number_of_pending_tasks": 3,
  "number_of_in_flight_fetch": 0,
  "task_max_waiting_in_queue_millis": 1200,
  "active_shards_percent_as_number": 95.2
}
```

Normalized `ClusterHealthSnapshot`:
```python
class ClusterHealthSnapshot(BaseModel):
    tier: Literal["T1"] = "T1"
    timestamp: datetime
    cluster_name: str
    status: Literal["green", "yellow", "red"]
    number_of_nodes: int
    number_of_data_nodes: int
    active_primary_shards: int
    active_shards: int
    relocating_shards: int
    initializing_shards: int
    unassigned_shards: int
    pending_tasks: int
    active_shards_percent: float
    # Raw response preserved for debugging
    _raw: dict | None = None
```

### 4.6 Snapshot Store

The Snapshot Store (`guardian/snapshots/`) is the shared in-memory (plus SQLite-persisted) buffer of the latest normalized snapshots from all tiers. It is the single source of truth that Doctor rules, the cost optimizer, and the UI streaming layer consume.

```
SnapshotStore
├── latest: dict[Tier, NormalizedSnapshot]   # most recent snapshot per tier
├── history: deque[SnapshotEntry]            # rolling window (configurable, default 1000 entries)
├── connection_id: UUID
├── push(snapshot) -> None                   # add to latest + history
├── get_latest(tier: Tier) -> NormalizedSnapshot | None
├── get_history(tier: Tier, since: datetime) -> list[NormalizedSnapshot]
└── subscribe(tier: Tier, callback) -> SubscriptionHandle
```

**Storage:**
- In-memory: `dict` + `deque` for the live snapshot window (fast access for Doctor rules).
- SQLite: Persistent history for trend analysis and before/after comparisons (e.g., provisioning validation).
- Memory-bounded: History is capped; oldest entries are evicted.

### 4.7 Streaming to Electron

The Snapshot Store publishes new snapshots to the Electron renderer via SSE (Server-Sent Events) or WebSocket. The streaming layer (`guardian/streaming/`) pushes events on:
- Every T1 snapshot (high frequency, small payload)
- Every T2 snapshot
- State-change events (incident detected/cleared, connection status changes)

The UI subscribes to specific tiers and filters by connection ID.

---

## 5. Module Structure

```
guardian/
├── connections/
│   ├── __init__.py
│   ├── profile.py            # ConnectionProfile model
│   ├── manager.py            # ConnectionManager: CRUD + lifecycle
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── base.py           # AuthAdapter protocol
│   │   ├── basic.py          # BasicAuthAdapter
│   │   ├── client_cert.py    # ClientCertAuthAdapter (V1.1)
│   │   └── custom_ca.py      # CustomCAAuthAdapter (V1.1)
│   ├── keychain.py           # OS keychain integration (keyring wrapper)
│   ├── tester.py             # ConnectionTest: version, identity, permissions, TLS
│   └── exceptions.py         # ConnectionError, AuthError, TLSError, etc.
├── collectors/
│   ├── __init__.py
│   ├── orchestrator.py       # CollectorOrchestrator
│   ├── tiers/
│   │   ├── __init__.py
│   │   ├── t1_live.py        # Cluster health, node status
│   │   ├── t2_trending.py    # Node stats, shard state
│   │   ├── t3_deep.py        # Index stats, cluster settings
│   │   └── t4_diagnostic.py  # Mappings, ILM, allocation explain
│   ├── normalizers/
│   │   ├── __init__.py
│   │   ├── base.py           # Normalizer protocol
│   │   ├── health.py         # Cluster health normalizer
│   │   ├── nodes.py          # Nodes stats normalizer
│   │   ├── shards.py         # Shard state normalizer
│   │   └── indices.py        # Index stats normalizer
│   ├── adaptive.py           # Incident-driven cadence adjustments
│   └── exceptions.py
├── snapshots/
│   ├── __init__.py
│   ├── store.py              # SnapshotStore: in-memory + SQLite
│   └── models.py             # Normalized snapshot Pydantic models
├── streaming/
│   ├── __init__.py
│   ├── sse.py                # SSE endpoint for Electron
│   └── websocket.py          # WebSocket endpoint (alternative)
└── exceptions.py
```

---

## 6. Interaction with Downstream Systems

### 6.1 Cluster Doctor (T16)

The Doctor reads from `SnapshotStore.get_latest(tier)` for its rule evaluation. Rules operate on normalized models, never raw API responses. The Doctor does not trigger collection — it consumes whatever the collector has collected.

### 6.2 Cost Optimizer (T17)

The Cost Optimizer subscribes to T3 and T4 snapshots. It may also trigger on-demand T5 collections for specific indices or nodes when investigating cost opportunities.

### 6.3 Provisioning Engine (T18/T20)

The Provisioning Engine reads the current snapshot (for before-state) and triggers on-demand T5 collections (for allocation explain, targeted diagnostics) during the provisioning workflow. It requires `write_enabled=true` and `provisioning_enabled=true` on the connection profile.

### 6.4 Electron UI (T15)

The UI subscribes to SSE/WebSocket events. It receives:
- Real-time snapshot data (T1, T2)
- Connection status changes (ACTIVE, FAILED, RECOVERING)
- Incident alerts (from adaptive mode transitions)
- Snapshot history for trend charts

---

## 7. Security & Safety

| Concern | Mitigation |
|---------|------------|
| Credentials in plaintext | OS keychain via `keyring`; never stored in SQLite or memory beyond session |
| TLS downgrade | TLS verification enabled by default; custom CA opt-in only |
| Excess permissions | Connection test reports exact permissions; UI warns if write role is detected on read-only profile |
| Credential leakage in logs | All logging uses redacted credential references; secrets never appear in log output |
| Connection hijacking | Each connection profile has a UUID; the orchestrator binds collectors to a specific connection ID |
| Man-in-the-middle | TLS certificate pinning is out of scope for V1; standard certificate validation is sufficient |

---

## 8. Error Handling & Resilience

| Error Type | Behavior |
|------------|----------|
| Connection refused / DNS failure | Retry with exponential backoff; transition to RECOVERING |
| TLS certificate error | Immediate transition to FAILED; surface error to user with details (expiry, hostname mismatch, untrusted CA) |
| Authentication failure | Immediate transition to FAILED; surface to user (credential reference logged, not secret) |
| Permission denied (read) | Connection test fails; profile cannot reach ACTIVE state |
| Permission denied (write) | Connection succeeds in read-only mode; write operations return 403 |
| Rate limiting (429) | Collector backs off for the rate-limit duration, then resumes |
| Timeout | Retry once with increased timeout; if still failing, log and skip this collection cycle |
| Malformed response | Log warning with raw response snippet; skip normalization for this cycle; do not crash the orchestrator |

---

## 9. OpenSearch API Reference

### 9.1 Tier 1 — Live (~5s)

| API | Purpose | opensearch-py method |
|-----|---------|---------------------|
| `GET /` | Version, cluster name | `client.info()` |
| `GET /_cluster/health` | Health status, shard counts | `client.cluster.health()` |
| `GET /_cat/nodes` | Node list with heap, JVM, CPU | `client.cat.nodes()` |
| `GET /_cat/thread_pool` | Thread pool activity | `client.cat.thread_pool()` |

### 9.2 Tier 2 — Trending (~10-15s)

| API | Purpose | opensearch-py method |
|-----|---------|---------------------|
| `GET /_nodes/stats` | JVM, CPU, mem, FS, OS per node | `client.nodes.stats()` |
| `GET /_cat/shards` | Shard allocation state | `client.cat.shards()` |
| `GET /_cat/recovery` | Ongoing shard recoveries | `client.cat.recovery()` |
| `GET /_cluster/state` | Cluster-level metadata (throttled) | `client.cluster.state()` |

### 9.3 Tier 3 — Deep (~30-60s)

| API | Purpose | opensearch-py method |
|-----|---------|---------------------|
| `GET /*` (indices) | Index list with docs, store size | `client.indices.get()` |
| `GET /_stats` | Index-level stats (docs, indexing, search) | `client.indices.stats()` |
| `GET /_cluster/settings` | Persistent + transient settings | `client.cluster.get_settings()` |

### 9.4 Tier 4 — Diagnostic (~5min)

| API | Purpose | opensearch-py method |
|-----|---------|---------------------|
| `GET /*/_mapping` | Field count, mapping explosion detection | `client.indices.get_mapping()` |
| `GET /_ilm/policy` | ILM policy status | `client.ilm.get_policy()` |
| `POST /*/_aliases` (sampled) | Allocation explain for unassigned shards | `client.cluster.allocation_explain()` |
| `GET /*/_segments` | Segment-level storage analysis | `client.indices.segments()` |

### 9.5 Tier 5 — On-demand

Any API accessible through the connection profile's permission scope. The UI or Doctor/Cost Optimizer requests a specific API call; the result is normalized and returned without persisting to the snapshot store (unless the user chooses to save it).

---

## 10. Configuration

The Connection Manager and Collector are configured via a combination of:
- **SQLite** (`guardian.db`): Connection profiles, snapshot history, audit log.
- **Environment variables**: Keychain service name, SQLite path, default cadence overrides.
- **Runtime config** (`config.yaml`): Optional overrides for cadence, adaptive thresholds, log levels.

No connection secrets appear in any configuration file.

---

## 11. Open Questions & Decisions Needed

1. **Phyllis's data-model / component-contract:** Once T7 lands, validate that the normalized snapshot models defined here align with the canonical internal models. Field-level reconciliation may be needed.
2. **SSE vs WebSocket:** This design assumes SSE as the primary streaming mechanism (simpler, sufficient for push-only). WebSocket is retained as an alternative. Decision to be confirmed with T15 (Electron architecture).
3. **Snapshot history window size:** 1000 entries is a default; should it be configurable? What is the memory budget?
4. **Connection profile encryption at rest:** SQLite database should be encrypted or the file should be protected by OS-level permissions. This is an operational concern, not a design concern, but should be noted.
5. **Multi-cluster support:** The design assumes one active connection at a time per CollectorOrchestrator, but the Connection Manager supports multiple profiles. The orchestrator should be instantiable per-profile. Clarify whether the UI will show multiple clusters simultaneously.

---

## 12. Definition of Done

- [x] Design document written and placed at `docs/architecture/connection-and-collection.md`
- [x] Aligned with SOP §3.1, §3.2, §4.2, §8
- [x] Consistent with ADR-001 (direct OpenSearch primary), ADR-002 (read-only default, write gating), ADR-003 (opensearch-py + FastAPI), ADR-004 (normalized models for Doctor), ADR-005 (tiered adaptive cadence)
- [ ] Pending: Review by phyllis-msyilmgq
- [ ] Pending: Alignment check against T7 deliverables (data-model.md, component-contract.md) when available
- [ ] Consumed by T13 (ConnectionManager + opensearch-py client implementation)

---

## Appendix A: Minimal Viable Connection Test Checklist

For the V1 connection test, the following five checks must all pass for a connection to reach ACTIVE state:

1. **HTTP reachability:** The endpoint responds to HTTPS requests.
2. **Version resolution:** `GET /` returns a valid OpenSearch version string.
3. **Cluster identity:** `GET /_cluster/health` returns a cluster name and UUID.
4. **Read permissions:** `GET /_nodes/stats` and `GET /_cluster/health` succeed without 403.
5. **TLS validity:** The certificate chain is valid and not expired (if TLS is enabled).

All five are mandatory. Warnings (e.g., self-signed cert with `tls_verify=false`, deprecated API versions) are surfaced to the user but do not block activation.

---

## Appendix B: Recommended Least-Privilege Monitoring Role

The following OpenSearch role grants the minimum permissions required for full read-only monitoring:

```json
{
  "cluster": [
    "monitor",
    "manage_index_lifecycle",
    "manage_slaves"
  ],
  "indices": [
    "monitor",
    "view_index_metadata",
    "read",
    "read_transform"
  ]
}
```

This role is provided as a reference template. The actual role name and index patterns should be configured per deployment. The Connection Manager's permission test will validate that a user with this role can access all required APIs.