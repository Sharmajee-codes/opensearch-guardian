# OpenSearch REST API Surface — Research & Coverage

**Author:** Phyllis (T7)
**Date:** 2026-08-19
**Purpose:** Define the REST API surface that the OpenSearch Collector normalizes, with coverage rationale, permission requirements, and version caveats.

---

## 1. API Inventory

### 1.1 Cluster Health API

**Endpoint:** `GET /` (root) and `GET /_cluster/health`

**Purpose:** Primary monitoring signal — cluster health status (green/yellow/red), number of nodes, shard allocation state, and pending tasks.

**Key response fields:**
- `status` — `green`, `yellow`, or `red`
- `number_of_nodes` — total nodes in the cluster
- `number_of_data_nodes` — data-capable nodes
- `active_primary_shards` — primaries currently allocated
- `active_shards` — all allocated shards (primary + replica)
- `relocating_shards` — shards currently moving between nodes
- `initializing_shards` — shards being created
- `unassigned_shards` — shards with no allocation (primary or replica)
- `pending_tasks` — cluster-wide tasks queued for execution
- `timed_out` — whether the response was truncated

**Permissions required:** Read-only; no special privileges needed beyond cluster-level read access.

**Version notes:**
- OpenSearch 1.x: Basic fields available. `delayed_unassigned_shards` present.
- OpenSearch 2.x: `relocating_shards` reporting improved; `delayed_start_time` for delayed allocation; `manually_cancelled_primary_shards` added in 2.3+.
- Query parameter `local=true` returns local node state without cluster-level coordination (faster, but may be stale).
- `wait_for_status=<level>` can block until the cluster reaches a threshold — useful for preflight checks but NOT for normal polling.

**Example request:**
```http
GET /_cluster/health?local=false&pretty=true
```

**Example response (abbreviated):**
```json
{
  "cluster_name": "guardian-test",
  "status": "yellow",
  "timed_out": false,
  "number_of_nodes": 3,
  "number_of_data_nodes": 3,
  "active_primary_shards": 10,
  "active_shards": 15,
  "relocating_shards": 0,
  "initializing_shards": 0,
  "unassigned_shards": 5,
  "pending_tasks": 0
}
```

---

### 1.2 Cluster Stats API

**Endpoint:** `GET /_cluster/stats`

**Purpose:** Cluster-wide aggregates — node counts, shard distribution, index counts, JVM heap usage, filesystem disk stats, and cluster-level settings.

**Key response fields:**
- `cluster_name` — cluster identifier
- `status` — cluster health at time of query
- `timed_out` — truncation flag
- `total_cells` — total nodes across all clusters (multi-cluster mode)
- `nodes` — counts by role (`data`, `ingest`, `master`, `voting_only`, `remote_cluster_client`, `ml`, `transform`)
- `indices` — index count, shard counts (total, prim, rep), doc counts, store size, field count
- `fs` — filesystem details: total/available/used disk per node, I/O stats
- `jvm` — heap used/committed/max across nodes (aggregated)
- `process` — CPU percent, open file descriptors, memory lock

**Permissions required:** Cluster-level `monitor` role or equivalent read access.

**Version notes:**
- OpenSearch 1.x: `nodes.discovered` field present (removed in 2.x in favor of role-based counts).
- OpenSearch 2.x: `indices.analysis` section added for analysis component stats; field count is more accurate.
- `flat_settings=true` returns settings as flat key-value pairs (easier to parse).

**Example request:**
```http
GET /_cluster/stats?human=true&pretty=true
```

---

### 1.3 Nodes Stats API

**Endpoint:** `GET /_nodes/stats` (all nodes) or `GET /_nodes/<node_id>/stats` (single node)

**Purpose:** Per-node deep metrics — JVM, OS, process, thread pool, HTTP, transport, indices, cache, and filesystem. This is the richest single API for monitoring.

**Key response sections:**
- `jvm` — heap used/committed/max, gc counts/durations (young/old), buffer pool stats, uptime
- `os` — CPU percent, load average, mem total/used/free, cgroup stats
- `process` — CPU total/time, open file descriptors, max file descriptors, mem swap
- `thread_pool` — per-pool: threads, queue, active, rejected, completed, leaked (critical for detecting thread starvation)
- `fs` — total/available/used disk per mount, I/O ops
- `indices` — index-level aggregates: doc count, store size, index buffer, flush, merge, refresh, search load
- `breakers` — circuit breaker stats (index, parent, request)
- `script` — compiled script cache, field data cache, completion cache

**Permissions required:** Cluster-level `monitor` role; some sections may require `cluster:admin/get` for full detail.

**Version notes:**
- OpenSearch 1.x: `thread_pool.leaked` detection available.
- OpenSearch 2.x: `jvm.memory_pools` more granular; `indices.request_cache` hit/miss ratios refined.
- `flat_settings=true` recommended for parsing.
- `metric=*` or specific metric paths (e.g., `_nodes/stats/jvm,os,process,fs`) can reduce payload size for frequent polling.

**Example request (lightweight, for 5s cadence):**
```http
GET /_nodes/stats/jvm,os,process,fs,thread_pool?flat_settings=true&human=true
```

**Example request (full, for 5min cadence):**
```http
GET /_nodes/stats?flat_settings=true&human=true
```

---

### 1.4 Nodes Info API

**Endpoint:** `GET /_nodes` and `GET /_nodes/<node_id>`

**Purpose:** Node metadata — roles, attributes, version, host, IP, JVM info, process info, plugins. Used for identity and configuration assessment.

**Key response fields:**
- `nodes.<id>.name` — node name
- `nodes.<id>.roles` — array of roles (`master`, `data`, `data_content`, `data_hot`, `data_warm`, `data_cold`, `data_frozen`, `ingest`, `ml`, `remote_cluster_client`, `transform`, `voting_only`)
- `nodes.<id>.version` — OpenSearch version string
- `nodes.<id>.host`, `nodes.<id>.ip` — network identity
- `nodes.<id>.attributes` — custom node attributes (e.g., `ml.max_machine_memory_size`)
- `nodes.<id>.jvm` — JVM version, pid, startup time, heap max

**Permissions required:** Cluster-level `monitor` role.

**Version notes:**
- OpenSearch 1.x: Role names differ (e.g., `data` instead of `data_content`/`data_hot` etc.). Use role mapping in the normalizer.
- OpenSearch 2.x: New roles `data_frozen`, `transform`, `voting_only`; `data` is deprecated in favor of content-specific roles.
- `local=true` returns the local node only (fastest option for node identity checks).

---

### 1.5 Cat APIs

**Endpoint:** `GET /_cat/<resource>?v=true`

**Purpose:** Human-readable tabular output for quick checks. Used for on-demand diagnostics, NOT for high-frequency polling (text parsing is fragile).

**Key APIs and their relevance:**

| API | Purpose | Cadence |
|-----|---------|---------|
| `/_cat/health` | Cluster health summary | On-demand / 5s if needed |
| `/_cat/nodes` | Node listing with roles, JVM, heap, disk | On-demand |
| `/_cat/indices` | Index listing with size, docs, shards | On-demand / 30–60s |
| `/_cat/shards` | Per-shard allocation detail | On-demand |
| `/_cat/allocation` | Disk allocation per node | On-demand |
| `/_cat/recovery` | Ongoing shard recovery progress | On-demand |
| `/_cat/tasks` | Running cluster tasks | On-demand |
| `/_cat/segments` | Index segment details (memory-heavy) | On-demand only |

**Permissions required:** Cluster-level `monitor` role.

**Version notes:**
- All cat APIs are stable across 1.x and 2.x with consistent column names.
- `h=<columns>` query parameter selects specific columns (useful for reducing payload).
- `s=<column>:desc` sorts output.

---

### 1.6 Shard Allocation Explain API

**Endpoint:** `POST /_cluster/allocation/explain`

**Purpose:** Explains why a specific shard is unassigned, started, or relocated. Critical for diagnosing shard placement failures.

**Key response fields:**
- `current_state` — `unassigned`, `started`, `relocating`
- `current_node` — node name hosting the shard (if started)
- `assigned_date` — when the shard was assigned
- `allocation_status` — `yes`, `no`, `delayed`, `deciders`
- `can_allocate` — whether the shard CAN be allocated
- `allocate_explanation` — human-readable reason
- `node_allocation_decisions` — per-node decision with decider names and reasons

**Permissions required:** Cluster-level `monitor` role.

**Version notes:**
- OpenSearch 1.x: Basic explain functionality.
- OpenSearch 2.x: More detailed decider explanations; `relocated_node` and `relocating_node` fields added.
- If no unassigned shards exist, the API returns `{"note": "No unassigned shards found."}` — handle gracefully.

**Example request:**
```http
POST /_cluster/allocation/explain
{
  "shard": 0,
  "index": "my-index"
}
```

---

### 1.7 Index Stats API

**Endpoint:** `GET /_stats` or `GET /<index>/_stats`

**Purpose:** Per-index statistics — document counts, store size, index buffer, search/load, flush, merge, refresh, query cache, filter cache.

**Key response fields:**
- `indices.<name>.uuid` — index UUID
- `indices.<name>.primaries` — primary shard aggregates
- `indices.<name>.total` — total (primary + replica) aggregates
- Fields per shard group: `docs.count`, `store.size`, `indexing.index_total`, `search.query_total`, `search.fetch_total`, `merges.total`, `refresh.total`, `buffer_size`

**Permissions required:** Index-level `monitor` or `indices:admin/get` permission.

**Version notes:**
- OpenSearch 1.x: `indices` field present in response; some cache stats are less detailed.
- OpenSearch 2.x: `search.fetch_low_level` added; `indexing_index_total_time` more accurate.
- Use `metric=store,docs,segments` to limit payload for frequent polling.

**Example request:**
```http
GET /_stats/store,docs,segments?human=true
```

---

### 1.8 Index Settings & Mappings API

**Endpoint:** `GET /<index>/_settings` and `GET /<index>/_mapping`

**Purpose:** Read current index configuration — shard/replica counts, refresh interval, codec, analyzer, field mappings. Used by the cost optimizer for retention/mapping analysis.

**Key fields (settings):**
- `number_of_shards`, `number_of_replicas`
- `refresh_interval`, `codec`, `routing`
- `index.lifecycle.name` (ILM policy reference)
- `index.blocks.read_only`, `index.blocks.read_only_allow_delete`

**Key fields (mappings):**
- `properties` — field definitions with types
- `dynamic` — dynamic mapping behavior
- ` _meta` — user-defined metadata

**Permissions required:** Index-level `monitor` or `indices:admin/get` permission.

**Version notes:**
- OpenSearch 1.x: Settings and mappings are in separate calls; `_all` field may be present (removed in 2.x).
- OpenSearch 2.x: `_all` field removed; `flattened` type available; `rank_feature` and `rank_features` types added.
- `flat_settings=true` simplifies parsing.

---

### 1.9 Cluster Settings API

**Endpoint:** `GET /_cluster/settings`

**Purpose:** Read effective cluster settings — transient, persistent, and default. Used to detect misconfiguration (e.g., `indices.recovery.max_bytes_per_sec` too low).

**Key fields:**
- `persistent` — settings that survive restart
- `transient` — settings that are lost on restart
- `defaults` — built-in defaults

**Permissions required:** Cluster-level `cluster:admin/get` or `monitor` role.

**Version notes:**
- Stable across 1.x and 2.x.
- `flat_settings=true` recommended.

---

### 1.10 Snapshot API (Read-Only)

**Endpoint:** `GET /_snapshot/<repository>/<snapshot>` and `GET /_snapshot/_all`

**Purpose:** List and inspect snapshots for capacity/cost analysis (snapshot storage usage, frequency, retention). Read-only access is sufficient.

**Permissions required:** `manage_snapshot` privilege (read portion) or cluster `monitor` role depending on configuration.

---

### 1.11 Remote Cluster Info (Multi-Cluster)

**Endpoint:** `GET /_remote_info`

**Purpose:** Report linked remote clusters in a cross-cluster search setup. Used for fleet/multi-cluster mode.

**Permissions required:** Cluster-level `monitor` role.

---

## 2. Permission Matrix

| API | Monitoring Role | Provisioning Role | Notes |
|-----|----------------|-------------------|-------|
| Cluster Health | ✅ Required | ✅ Included | Base requirement |
| Cluster Stats | ✅ Required | ✅ Included | |
| Nodes Stats | ✅ Required | ✅ Included | Full payload at 5-min cadence |
| Nodes Info | ✅ Required | ✅ Included | Role mapping required |
| Cat APIs | ✅ Required | ✅ Included | On-demand only |
| Shard Allocation Explain | ✅ Required | ✅ Included | On-demand |
| Index Stats | ✅ Required | ✅ Included | On-demand / 30-60s |
| Index Settings/Mappings | ✅ Required | ✅ Included | On-demand / 5-min |
| Cluster Settings | ✅ Required | ✅ Included | On-demand |
| Snapshot (read) | ✅ Optional | ✅ Included | If snapshots exist |
| Remote Info | ✅ Optional | ✅ Included | If multi-cluster |

**Minimal monitoring role should include:** `cluster:monitor/main`, `cluster:monitor/stats`, `cluster:monitor/state`, `cluster:admin/plugins/compatibility`, `indices:admin/get`, `indices:monitor/stats`, `indices:monitor/settings`, `indices:monitor/mappings`, `cluster:admin/analysis/analyze`.

---

## 3. OpenSearch 1.x vs 2.x Caveats

| Area | 1.x | 2.x | Impact on Guardian |
|------|-----|-----|-------------------|
| Node roles | `data`, `master`, `ingest` | Content-specific: `data_content`, `data_hot`, `data_warm`, `data_frozen`, `transform`, `voting_only` | Normalizer must map old roles to new taxonomy |
| `_all` field | Present by default | Removed | Mapping normalizer must handle absence |
| `nodes.discovered` | Present in cluster stats | Removed | Use role-based counts instead |
| `analysis` section | Not in cluster stats | Added | New data source for optimizer |
| `shard.allocation.total` | Basic | Enhanced with `delayed` and `manually_cancelled` | Update rule thresholds |
| REST API base path | `/` and `/<index>` | Same | No breaking changes for Guardian |

---

## 4. Collector Implementation Guidance

The `collectors/` module should implement the following normalization strategy:

1. **Tier 1 (~5s):** Call `GET /_cluster/health?local=true` and `GET /_nodes?local=true`. Parse into `ClusterSnapshot` and `NodeSnapshot` (identity only).
2. **Tier 2 (~10-15s):** Call `GET /_nodes/stats/jvm,os,process,fs,thread_pool?flat_settings=true&human=true`. Parse into `NodeSnapshot` (full metrics).
3. **Tier 3 (~30-60s):** Call `GET /_stats/store,docs,segments?human=true` and `GET /_cluster/settings?flat_settings=true`. Parse into `IndexSnapshot` and cluster settings.
4. **Tier 4 (~5min):** Call full `GET /_nodes/stats` and `GET /_cluster/stats`. Run full cost optimizer scan.
5. **On-demand:** Call `POST /_cluster/allocation/explain`, `GET /<index>/_mapping`, `GET /<index>/_settings`.

All responses pass through a `VersionAwareNormalizer` that handles 1.x → 2.x field differences before producing the internal models defined in `data-model.md`.

---

## 5. References

- OpenSearch Cluster Health API: https://docs.opensearch.org/latest/opensearch/rest-api/cluster-health/
- OpenSearch Cluster Stats API: https://docs.opensearch.org/latest/api-reference/cluster-api/cluster-stats/
- OpenSearch Nodes Stats API: https://docs.opensearch.org/latest/api-reference/nodes-apis/nodes-stats/
- OpenSearch Shard Allocation Explain: https://docs.opensearch.org/latest/api-reference/cluster-api/shard-allocation-explain/
- OpenSearch Index Stats: https://docs.opensearch.org/latest/api-reference/index-apis/stats/
- ADR-001 (Primary Data Plane), ADR-005 (Tiered Collection)
