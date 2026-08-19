# Data Model — Normalized Internal Models

**Author:** Phyllis (T7)
**Date:** 2026-08-19
**Purpose:** Define the version-agnostic internal data models that decouple Guardian's rules and optimizers from OpenSearch API version differences (per SOP §4.2, ADR-005).

---

## Design Principles

1. **Version-agnostic:** Models must produce the same shape regardless of whether the source is OpenSearch 1.x or 2.x.
2. **Unit-normalized:** All quantities use standard units (bytes, seconds, percent, count) with human-readable variants available.
3. **Immutable snapshots:** Each snapshot captures a point-in-time view; mutations produce new snapshots, not in-place edits.
4. **Evidence-linked:** Every finding and recommendation references the snapshot and field that triggered it.
5. **Pydantic v2:** All models use Pydantic v2 for validation, serialization, and OpenAPI generation.

---

## 1. ClusterSnapshot

A point-in-time view of the entire cluster's health and high-level state.

```python
class ClusterSnapshot(BaseModel):
    snapshot_id: str                    # UUID, unique per collection cycle
    cluster_name: str
    collected_at: datetime              # UTC timestamp of collection
    health_status: Literal["green", "yellow", "red"]
    
    # Node counts
    total_nodes: int
    data_nodes: int
    master_nodes: int
    ingest_nodes: int
    
    # Shard allocation
    active_primary_shards: int
    active_shards: int
    relocating_shards: int
    initializing_shards: int
    unassigned_shards: int
    delayed_unassigned_shards: int      # 2.x; 0 for 1.x
    
    # Pending work
    pending_cluster_tasks: int
    failed_cluster_tasks: int           # 2.x; absent in 1.x → 0
    
    # Source API
    source_api: str                     # "_cluster/health"
    source_version: str                 # e.g., "2.11.1"
    raw_response_hash: str              # SHA-256 of raw response for audit
```

**Version normalization notes:**
- `delayed_unassigned_shards`: 0 if not present in 1.x response.
- `failed_cluster_tasks`: 0 if not present in 1.x response.
- `initializing_shards` in 2.x includes shards in `STARTED` state on new nodes — same semantics as 1.x `initializing_shards`.

---

## 2. NodeSnapshot

Per-node metrics. One `NodeSnapshot` per node in the cluster.

```python
class JvmSnapshot(BaseModel):
    mem_heap_used_bytes: int
    mem_heap_max_bytes: int
    mem_heap_used_percent: int
    mem_non_heap_used_bytes: int
    gc_collectors_young_count: int
    gc_collectors_young_time_ms: int
    gc_collectors_old_count: int
    gc_collectors_old_time_ms: int
    buffer_pools_direct_count: int
    buffer_pools_direct_used_bytes: int
    buffer_pools_mapped_count: int
    buffer_pools_mapped_used_bytes: int
    uptime_ms: int

class OsSnapshot(BaseModel):
    cpu_percent: float
    load_average_1m: float
    load_average_5m: float
    load_average_15m: float
    mem_total_bytes: int
    mem_used_bytes: int
    mem_free_bytes: int
    mem_free_percent: int
    mem_used_percent: int
    cgroup_cpu_percent: Optional[float] = None  # Linux cgroup; absent on macOS/Windows

class ProcessSnapshot(BaseModel):
    cpu_percent: float
    cpu_total_ms: int
    open_file_descriptors: int
    max_file_descriptors: int
    mem_swap_used_bytes: int
    mem_swap_max_bytes: int

class ThreadPoolSnapshot(BaseModel):
    name: str                           # e.g., "write", "search", "management"
    threads: int
    queue: int
    active: int
    rejected: int
    completed: int
    leaked: int                         # 2.x; count of threads that held a listener too long

class FilesystemSnapshot(BaseModel):
    total_bytes: int
    available_bytes: int
    used_bytes: int
    available_percent: float
    disk_reads: int
    disk_writes: int
    disk_total_size_bytes: int

class NodeSnapshot(BaseModel):
    node_id: str
    node_name: str
    host: str
    ip: str
    roles: list[str]                    # Normalized role names (see role mapping table)
    version: str
    collected_at: datetime
    
    jvm: JvmSnapshot
    os: OsSnapshot
    process: ProcessSnapshot
    thread_pools: dict[str, ThreadPoolSnapshot]
    filesystems: list[FilesystemSnapshot]
    
    # Optional: index-level aggregates for this node
    indices_doc_count: Optional[int] = None
    indices_store_size_bytes: Optional[int] = None
    
    source_api: str                     # "_nodes/stats"
    source_version: str
    raw_response_hash: str
```

**Role normalization (OpenSearch 1.x → Guardian canonical roles):**

| 1.x Role | 2.x Role | Guardian Canonical |
|----------|----------|-------------------|
| `master` | `master` | `master` |
| `data` | `data_content`, `data_hot`, `data_warm`, `data_frozen` | `data` |
| `data` | `data` | `data` |
| `ingest` | `ingest` | `ingest` |
| — | `remote_cluster_client` | `remote_client` |
| — | `ml` | `ml` |
| — | `transform` | `transform` |
| — | `voting_only` | `voting_only` |

---

## 3. ShardState

Represents the state of an individual shard, used by the Doctor and rebalance monitor.

```python
class ShardState(BaseModel):
    shard_id: str                       # e.g., "0", "1", or index-specific ID
    index_name: str
    primary: bool
    node_id: Optional[str] = None       # None if unassigned
    node_name: Optional[str] = None
    state: Literal["STARTED", "INITIALIZING", "RELOCATING", "UNASSIGNED"]
    relocation_status: Optional[Literal["RELOCATING", "CANCELLED"]] = None
    primary_node_id: Optional[str] = None
    replica_node_id: Optional[str] = None
    
    # Size and docs
    store_size_bytes: Optional[int] = None
    primary_size_bytes: Optional[int] = None
    doc_count: Optional[int] = None
    
    # Recovery info (if applicable)
    recovery_source_node: Optional[str] = None
    recovery_target_node: Optional[str] = None
    recovery_progress_percent: Optional[float] = None
    
    # Allocation explanation (if unassigned)
    allocation_explanation: Optional[str] = None
    
    collected_at: datetime
```

---

## 4. IndexSnapshot

Per-index metrics used by the cost optimizer and capacity planner.

```python
class IndexSnapshot(BaseModel):
    index_name: str
    uuid: str
    collected_at: datetime
    
    # Document stats
    doc_count: int
    deleted_doc_count: int
    
    # Storage
    store_size_bytes: int
    primary_size_bytes: int
    
    # Shard configuration
    number_of_shards: int
    number_of_replicas: int
    total_shards: int                   # number_of_shards * (number_of_replicas + 1)
    
    # Search and indexing load
    search_query_total: int
    search_query_time_ms: int
    indexing_index_total: int
    indexing_index_time_ms: int
    
    # Segment info
    segment_count: int
    segment_memory_bytes: int
    
    # Settings
    refresh_interval_ms: int
    codec: str
    lifecycle_policy: Optional[str] = None
    read_only: bool
    read_only_allow_delete: bool
    
    # Mappings summary (lightweight — full mapping in separate model)
    field_count: int
    has_keyword_explosion: bool         # True if >10000 mapping fields
    
    source_api: str                     # "_stats" or "_settings" or "_mapping"
    source_version: str
    raw_response_hash: str
```

---

## 5. ClusterSettings

Effective cluster settings, used by the Doctor to detect misconfiguration.

```python
class ClusterSettings(BaseModel):
    collected_at: datetime
    persistent: dict[str, Any]          # Flat key-value pairs
    transient: dict[str, Any]
    defaults: dict[str, Any]
    
    # Normalized key points the Doctor cares about
    discovery_seed_hosts: list[str]
    cluster_routing_allocation_enable: str
    indices_recovery_max_bytes_per_sec: str  # e.g., "40mb"
    cluster_max_shards_per_node: Optional[int] = None
    indices_fielddata_cache_size: Optional[str] = None
```

---

## 6. Finding

A diagnostic finding produced by the rule engine. The core output of the Cluster Doctor.

```python
class Finding(BaseModel):
    finding_id: str                     # UUID
    rule_id: str                        # e.g., "RULE-001", "RULE-DISK-01"
    rule_name: str
    severity: Literal["critical", "high", "medium", "low", "info"]
    confidence: float                   # 0.0 to 1.0
    entity_type: Literal["cluster", "node", "shard", "index", "setting"]
    entity_id: str                      # node_id, index_name, shard_id, etc.
    
    # The diagnosis
    observed_value: Any
    threshold_or_expected: Any
    condition_description: str          # Human-readable condition that triggered this
    
    # Evidence — direct references to snapshot data
    evidence: list[EvidenceRef]
    
    # Actionability
    remediation_guidance: str
    safety_level: Literal[
        "informational",
        "safe_reversible",
        "approval_required",
        "destructive"
    ]
    
    # Lifecycle
    first_seen_at: datetime
    last_seen_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by_snapshot_id: Optional[str] = None  # Must be set before resolution
    
    # Correlation
    correlated_with: list[str] = []     # Other finding IDs
    
    snapshot_id: str                    # Which snapshot triggered this
```

**EvidenceRef:**
```python
class EvidenceRef(BaseModel):
    source_api: str                     # e.g., "_cluster/health"
    field_path: str                     # e.g., "unassigned_shards"
    observed_value: Any
    timestamp: datetime
```

---

## 7. Recommendation

An action recommendation, produced by the Doctor (via findings) or the Cost Optimizer.

```python
class Recommendation(BaseModel):
    recommendation_id: str              # UUID
    finding_ids: list[str] = []         # Related findings (empty for optimizer-only recs)
    type: Literal[
        "diagnostic",
        "storage_reclaim",
        "shard_reduction",
        "replica_optimization",
        "mapping_optimization",
        "capacity_recovery",
        "retention_optimization",
        "tiering_recommendation"
    ]
    title: str
    description: str
    assumed_confidence: float           # 0.0 to 1.0
    assumptions: list[str]              # Explicitly stated assumptions
    
    # Impact estimates (never exact currency in V1)
    estimated_storage_reclaim_bytes: Optional[int] = None
    estimated_shard_reduction_count: Optional[int] = None
    estimated_cost_savings_description: Optional[str] = None  # Text, not a number
    
    # Actionability
    safety_level: Literal[
        "informational",
        "safe_reversible",
        "approval_required",
        "destructive"
    ]
    required_permissions: list[str]
    estimated_risk: str
    
    created_at: datetime
```

---

## 8. ProvisioningPlan

The structured plan for a provisioning action, produced at the Plan stage (SOP §7, step 3) and reviewed at the Review stage (step 5).

```python
class ProvisioningPlan(BaseModel):
    plan_id: str                        # UUID
    cluster_name: str
    created_at: datetime
    created_by: str                     # User identity
    
    # Requested change
    requested_role: str
    requested_count: int
    requested_cpu_cores: int
    requested_memory_bytes: int
    requested_heap_bytes: Optional[int] = None
    requested_storage_bytes: int
    requested_version: Optional[str] = None
    
    # Guardian's analysis
    guardian_recommendation: str
    expected_impact: str                # Human-readable impact description
    rebalance_impact_estimate: str      # Estimated shard movement
    rollback_approach: str              # How to undo if things go wrong
    
    # Preflight results (populated at step 4)
    preflight_checks: list[PreflightCheck]
    preflight_passed: bool
    
    # Approval (populated at step 6)
    approval_required: bool
    approval_given_at: Optional[datetime] = None
    approval_given_by: Optional[str] = None
    
    # State
    current_state: str                  # Matches ProvisioningState enum
```

**PreflightCheck:**
```python
class PreflightCheck(BaseModel):
    check_name: str
    check_type: Literal["credential", "permission", "version", "network", "storage", "capacity", "security"]
    status: Literal["pass", "fail", "warning", "skipped"]
    message: str
```

---

## 9. Role Mapping Table

To maintain version-agnostic models, the collector normalizes OpenSearch node roles:

| Guardian Canonical Role | OpenSearch 1.x | OpenSearch 2.x | Description |
|------------------------|----------------|----------------|-------------|
| `master` | `master` | `master` | Cluster management |
| `data` | `data` | `data_content`, `data_hot`, `data_warm`, `data_frozen` | Index data storage |
| `ingest` | `ingest` | `ingest` | Document preprocessing |
| `remote_client` | — | `remote_cluster_client` | Cross-cluster search |
| `ml` | — | `ml` | Machine learning |
| `transform` | — | `transform` | Data transformation |
| `voting_only` | — | `voting_only` | Election-only master node |

---

## 10. Model Relationships

```
ClusterSnapshot
  ├── contains ──► NodeSnapshot (many)
  ├── contains ──► ShardState (many)
  ├── contains ──► IndexSnapshot (many)
  └── feeds ────► ClusterSettings

ClusterSnapshot + NodeSnapshot + ShardState + IndexSnapshot
  └── feeds ────► Diagnosis (produces Finding list)

Finding (many)
  └── feeds ────► Recommendation (many)

IndexSnapshot (many)
  └── feeds ────► Recommendation (optimizer types)

ProvisioningPlan
  ├── references ──► ClusterSnapshot (before state)
  ├── produces ──► ProvisioningAudit
  └── verified by ──► ClusterSnapshot (after state)
```

---

## 11. Serialization

All models serialize to JSON for IPC transmission and persistence. Pydantic v2's `model_dump(mode="json")` is used. Key serialization rules:

- `datetime` fields serialize to ISO 8601 with UTC timezone
- `bytes` fields serialize to base64 (for raw response hashes)
- `Optional` fields omit `null` when using `model_dump(exclude_none=True)` for IPC
- All models include `source_version` for traceability

---

## 12. References

- SOP §4.2 — Collection strategy
- ADR-005 — Tiered Adaptive Collection Cadence
- ADR-004 — Evidence-First Deterministic Cluster Doctor
- ADR-006 — Provisioning State Machine
- OpenSearch API research: `docs/architecture/research/opensearch-apis.md`
