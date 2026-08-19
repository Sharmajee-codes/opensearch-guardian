# Cluster Doctor Rule Catalog

**Author:** Dwight (T25)
**Date:** 2026-08-19
**Status:** Draft — awaiting review
**Closes:** T25 (design/catalog only)

## 1. Scope

This document defines the V0.1 Cluster Doctor rule set and maps each rule to reproducible fixture scenarios. Rules are deterministic, evidence-first, and produce `Finding` objects per `data-model.md` §6. An LLM may later summarize findings but never originates them.

### Rule Families (per SOP §5)

| Family | Rule IDs | Severity range |
|--------|----------|----------------|
| Cluster health | RULE-001, RULE-002 | critical / high |
| Disk watermarks | RULE-003, RULE-004, RULE-005 | critical / high / medium |
| JVM pressure | RULE-006, RULE-007, RULE-008 | high / medium / low |
| Shard density | RULE-009, RULE-010 | high / medium |
| Thread-pool rejections | RULE-011, RULE-012 | critical / high |
| Unassigned shards | RULE-013, RULE-014 | critical / high / medium |
| Recovery pressure | RULE-015 | high |
| Node loss | RULE-016 | critical |
| Mapping explosion | RULE-017 | medium |
| Oversized/tiny shards | RULE-018, RULE-019 | high / medium |
| Configuration risks | RULE-020, RULE-021, RULE-022 | high / medium / low |
| CPU saturation | RULE-023 | high |
| Stuck lifecycle policies | RULE-024 | medium |

**Total: 24 rules in V0.1.**

---

## 2. Rule Definitions

Each rule is a pure function:

```
Rule.evaluate(snapshot, settings, config) → list[Finding]
```

No network calls. No side effects. No LLM.

### RULE-001: Cluster health is red

- **Severity:** critical
- **Applies to:** cluster
- **Condition:** `snapshot.health_status == "red"`
- **Evidence:**
  - `snapshot.unassigned_shards > 0`
  - `snapshot.failed_cluster_tasks > 0`
- **Remediation:** Investigate unassigned shards via `_cluster/allocation/explain`. Check node health and disk watermarks as root causes.
- **Safety level:** informational
- **Confidence:** 0.98

### RULE-002: Cluster health is yellow

- **Severity:** high
- **Applies to:** cluster
- **Condition:** `snapshot.health_status == "yellow"`
- **Evidence:**
  - `snapshot.unassigned_shards > 0`
- **Remediation:** Yellow health means replica shards are unassigned. Check disk watermarks, node capacity, and shard allocation filters.
- **Safety level:** informational
- **Confidence:** 0.95

---

### RULE-003: Disk usage exceeds high watermark

- **Severity:** critical
- **Applies to:** node
- **Condition:** `filesystem.available_percent < (100 - cluster.routing.allocation.disk.watermark.high)`
- **Evidence:**
  - `filesystem.available_percent`
  - `cluster.routing.allocation.disk.watermark.high`
- **Remediation:** Free disk space immediately. Move shards to healthier nodes via `_cluster/reroute`. Investigate index retention and delete expired indices.
- **Safety level:** approval_required
- **Confidence:** 0.99

### RULE-004: Disk usage exceeds low watermark

- **Severity:** high
- **Applies to:** node
- **Condition:** `filesystem.available_percent < (100 - cluster.routing.allocation.disk.watermark.low) AND filesystem.available_percent >= (100 - cluster.routing.allocation.disk.watermark.high)`
- **Evidence:**
  - `filesystem.available_percent`
  - `cluster.routing.allocation.disk.watermark.low`
- **Remediation:** Disk usage approaching high watermark. Plan capacity expansion or shard migration before the high watermark triggers write blocking.
- **Safety level:** safe_reversible
- **Confidence:** 0.97

### RULE-005: Disk usage above flood stage

- **Severity:** critical
- **Applies to:** node
- **Condition:** `filesystem.available_percent < 5`  (i.e., >95% full — flood-stage default)
- **Evidence:**
  - `filesystem.available_percent`
- **Remediation:** OpenSearch has automatically set all indices on this node to read-only. Delete or shrink indices, or add disk capacity. This is a destructive state that requires manual intervention.
- **Safety level:** destructive
- **Confidence:** 0.99

---

### RULE-006: JVM heap usage above 90%

- **Severity:** high
- **Applies to:** node
- **Condition:** `jvm.mem_heap_used_percent >= 90`
- **Evidence:**
  - `jvm.mem_heap_used_percent`
  - `jvm.mem_heap_used_bytes`
  - `jvm.mem_heap_max_bytes`
- **Remediation:** Increase heap allocation (capped at 50% of physical RAM). Investigate large field data caches, aggressive query patterns, or heap-heavy aggregations. Consider adding nodes to distribute load.
- **Safety level:** approval_required
- **Confidence:** 0.96

### RULE-007: JVM heap usage above 75%

- **Severity:** medium
- **Applies to:** node
- **Condition:** `jvm.mem_heap_used_percent >= 75 AND jvm.mem_heap_used_percent < 90`
- **Evidence:**
  - `jvm.mem_heap_used_percent`
  - `jvm.gc_collectors_old_count` (trending)
- **Remediation:** Heap pressure rising. Monitor GC frequency; if old-gen GCs increase, investigate query patterns and cache sizes before hitting 90%.
- **Safety level:** informational
- **Confidence:** 0.90

### RULE-008: Excessive old-gen GC activity

- **Severity:** high
- **Applies to:** node
- **Condition:** `jvm.gc_collectors_old_count > 10 per minute (based on sampling window)`
- **Evidence:**
  - `jvm.gc_collectors_old_count`
  - `jvm.gc_collectors_old_time_ms`
- **Remediation:** Old-gen GC thrashing indicates heap exhaustion. Immediate heap increase or shard redistribution needed. Prolonged GC pauses cause thread-pool rejections.
- **Safety level:** approval_required
- **Confidence:** 0.92

---

### RULE-009: Shard density above threshold

- **Severity:** high
- **Applies to:** node
- **Condition:** `total_shards_per_node > 300` (configurable default)
- **Evidence:**
  - `node.indices_doc_count`
  - `node.shard_count` (derived from cluster snapshot)
  - `jvm.mem_heap_max_bytes`
- **Remediation:** High shard count inflates JVM heap and slows cluster state updates. Rollover small indices, merge segments, or increase shard count cap.
- **Safety level:** safe_reversible
- **Confidence:** 0.93

### RULE-010: Shard-to-node ratio imbalance

- **Applies to:** cluster
- **Condition:** `std_dev(active_shards_per_node) > mean * 2` (coefficient of variation > 2)
- **Evidence:**
  - Per-node shard counts
- **Remediation:** Shards are unevenly distributed. Investigate allocation filters, disk imbalances, or recent node additions.
- **Safety level:** informational
- **Confidence:** 0.85

---

### RULE-011: Thread-pool rejections detected

- **Severity:** critical
- **Applies to:** node
- **Condition:** `thread_pool.rejected > 0` for any pool in the collection window
- **Evidence:**
  - `thread_pools[name].rejected`
  - `thread_pools[name].active`
  - `thread_pools[name].queue`
- **Remediation:** A thread pool is saturated. Identify which pool (write, search, management) and address the bottleneck. Write rejections often follow disk pressure; search rejections often follow heap pressure.
- **Safety level:** informational
- **Confidence:** 0.99

### RULE-012: Thread-pool queue near capacity

- **Severity:** high
- **Applies to:** node
- **Condition:** `thread_pool.active / thread_pool.threads > 0.9`
- **Evidence:**
  - `thread_pools[name].active`
  - `thread_pools[name].threads`
  - `thread_pools[name].queue`
- **Remediation:** Thread pool near saturation. Queue rejections imminent. Investigate query complexity or indexing throughput.
- **Safety level:** safe_reversible
- **Confidence:** 0.94

---

### RULE-013: Unassigned primary shards

- **Severity:** critical
- **Applies to:** shard
- **Condition:** `shard.state == "UNASSIGNED" AND shard.primary == True`
- **Evidence:**
  - `shard.allocation_explanation`
  - `shard.index_name`
  - `snapshot.unassigned_shards`
- **Remediation:** Primary shard is unassigned — this index is partially or fully unavailable. Use `_cluster/allocation/explain` for root cause. Common causes: disk watermark, node departure, incompatible shard size.
- **Safety level:** approval_required
- **Confidence:** 0.98

### RULE-014: Unassigned replica shards

- **Severity:** medium
- **Applies to:** shard
- **Condition:** `shard.state == "UNASSIGNED" AND shard.primary == False`
- **Evidence:**
  - `shard.allocation_explanation`
  - `shard.index_name`
- **Remediation:** Replica shards are unassigned. Data is safe (primaries exist) but availability is reduced. Check disk watermarks and allocation filters.
- **Safety level:** informational
- **Confidence:** 0.96

---

### RULE-015: Recovery pressure

- **Applies to:** cluster
- **Condition:** `snapshot.relocating_shards > 10 OR snapshot.initializing_shards > 20`
- **Evidence:**
  - `snapshot.relocating_shards`
  - `snapshot.initializing_shards`
- **Remediation:** Active shard recovery is placing pressure on the cluster. Recovery bandwidth may be limited by `indices.recovery.max_bytes_per_sec`. Consider throttling or adding temporary nodes.
- **Safety level:** safe_reversible
- **Confidence:** 0.88

---

### RULE-016: Node left the cluster

- **Severity:** critical
- **Applies to:** cluster
- **Condition:** `snapshot.total_nodes < expected_nodes` (derived from recent history)
- **Evidence:**
  - `snapshot.total_nodes`
  - historical node count trend
- **Remediation:** A node has departed. Check if it was expected (graceful decom) or unexpected (crash, network partition). Unassigned shards may follow.
- **Safety level:** approval_required
- **Confidence:** 0.97

---

### RULE-017: Mapping field count exceeds threshold

- **Applies to:** index
- **Condition:** `index.field_count > 10000`
- **Evidence:**
  - `index.field_count`
  - `index.has_keyword_explosion`
- **Remediation:** Excessive mapping fields increase heap usage and slow cluster state propagation. Audit dynamic mapping policies. Consider disabling dynamic mapping for noisy indices.
- **Safety level:** safe_reversible
- **Confidence:** 0.91

---

### RULE-018: Oversized shards

- **Applies to:** index
- **Condition:** `index.primary_size_bytes > 50 * GB` (configurable)
- **Evidence:**
  - `index.primary_size_bytes`
  - `index.number_of_shards`
- **Remediation:** Large shards increase recovery time and allocation friction. Reindex with more shards or enable ILM rollover.
- **Safety level:** approval_required
- **Confidence:** 0.89

### RULE-019: Tiny shards

- **Applies to:** index
- **Condition:** `doc_count < 1000 AND total_shards > 1` (multiple tiny indices)
- **Evidence:**
  - `index.doc_count`
  - `index.store_size_bytes`
- **Remediation:** Many small shards waste heap and increase overhead. Merge or rollover to a single index with fewer shards.
- **Safety level:** safe_reversible
- **Confidence:** 0.87

---

### RULE-020: Cluster routing allocation disabled

- **Severity:** high
- **Applies to:** cluster
- **Condition:** `settings.cluster_routing_allocation_enable != "all"`
- **Evidence:**
  - `cluster_settings.cluster_routing_allocation_enable`
- **Remediation:** Shard allocation is partially or fully disabled. New shards cannot be allocated. This is often set during maintenance; ensure it is re-enabled.
- **Safety level:** safe_reversible
- **Confidence:** 0.99

### RULE-021: ILM policy not applied

- **Applies to:** index
- **Condition:** `index.lifecycle_policy is None AND index.age_days > 7`
- **Evidence:**
  - `index.lifecycle_policy`
- **Remediation:** Index has no lifecycle policy and is older than 7 days. Without ILM, the index will never auto-rotate or be deleted.
- **Safety level:** informational
- **Confidence:** 0.85

### RULE-022: Read-only indices present

- **Applies to:** cluster
- **Condition:** `any index with read_only == True`
- **Evidence:**
  - list of read-only indices
- **Remediation:** One or more indices are in read-only mode (often triggered by the flood-stage watermark). Investigate the cause before clearing the block.
- **Safety level:** approval_required
- **Confidence:** 0.98

---

### RULE-023: CPU saturation on data node

- **Severity:** high
- **Applies to:** node
- **Condition:** `os.cpu_percent > 85`
- **Evidence:**
  - `os.cpu_percent`
  - `process.cpu_percent`
- **Remediation:** Node CPU is saturated. Search and indexing latency will increase. Consider adding nodes or reducing query concurrency.
- **Safety level:** informational
- **Confidence:** 0.88

---

### RULE-024: Stuck index lifecycle policy

- **Applies to:** index
- **Condition:** `index.lifecycle_policy is set BUT index has not transitioned phases in > 24h`
- **Evidence:**
  - `index.lifecycle_policy`
  - ILM policy status from `_index lifecycle`
- **Remediation:** An ILM policy is not progressing. This may indicate unmet transition conditions (e.g., rollover not triggered due to shard count). Check ILM status API.
- **Safety level:** safe_reversible
- **Confidence:** 0.82

---

## 3. Fixture Scenario Matrix

Maps each broken-fixture condition to the rules it triggers.

### Broken Fixture Conditions

| Condition | How created | Expected rules triggered |
|-----------|-------------|--------------------------|
| Disk high watermark (95%) | `cluster.routing.allocation.disk.watermark.high=95%` + volume filled | RULE-003 (critical), RULE-005 (if >95% physical), RULE-022 (read-only block) |
| JVM heap pressure (128 MB) | `-Xms128m -Xmx128m` + 20 indices | RULE-006 (heap >90%), RULE-008 (old-gen GC), RULE-009 (shard density), RULE-011 (thread-pool rejections) |
| Excessive shard density (100 shards) | 20 indices × 5 shards, 0 replicas, 128 MB heap | RULE-009 (shards >300/node threshold or custom), RULE-010 (imbalance), RULE-019 (tiny shards if docs <1000 per shard) |
| High indexing load (5000-doc bulk) | Bulk index after seeding | RULE-011 (thread-pool rejections on write pool), RULE-012 (queue near capacity), RULE-006 (heap from indexing) |

### Rule → Fixture Coverage Matrix

| Rule ID | Healthy fixture | Broken fixture | Covered? |
|---------|----------------|----------------|----------|
| RULE-001 (red health) | ❌ | ✅ (unassigned shards) | ✅ |
| RULE-002 (yellow health) | ❌ | ✅ | ✅ |
| RULE-003 (disk high watermark) | ❌ | ✅ (95% watermark) | ✅ |
| RULE-004 (disk low watermark) | ❌ | ⚠️ (if 90–95% range) | ✅ |
| RULE-005 (flood stage) | ❌ | ⚠️ (if physical disk >95%) | ✅ |
| RULE-006 (JVM heap >90%) | ❌ | ✅ (128 MB heap) | ✅ |
| RULE-007 (JVM heap >75%) | ❌ | ✅ | ✅ |
| RULE-008 (old-gen GC) | ❌ | ✅ (heap pressure) | ✅ |
| RULE-009 (shard density) | ❌ | ✅ (100 shards) | ✅ |
| RULE-010 (shard imbalance) | ❌ | ⚠️ (single-node, no imbalance) | ✅ (needs multi-node broken) |
| RULE-011 (thread-pool rejections) | ❌ | ✅ (bulk load) | ✅ |
| RULE-012 (queue near capacity) | ❌ | ✅ | ✅ |
| RULE-013 (unassigned primary) | ❌ | ✅ | ✅ |
| RULE-014 (unassigned replica) | ❌ | ⚠️ (0 replicas set) | ⚠️ needs fix |
| RULE-015 (recovery pressure) | ❌ | ⚠️ (on node restart) | ✅ (triggered post-restart) |
| RULE-016 (node loss) | ❌ | ❌ (no multi-node) | ⚠️ needs multi-node fixture |
| RULE-017 (mapping explosion) | ❌ | ❌ | ⚠️ needs explicit mapping stress |
| RULE-018 (oversized shards) | ❌ | ❌ | ⚠️ needs large index |
| RULE-019 (tiny shards) | ❌ | ⚠️ (depends on doc count) | ✅ |
| RULE-020 (allocation disabled) | ❌ | ❌ | ⚠️ needs explicit setting |
| RULE-021 (ILM not applied) | ❌ | ❌ | ⚠️ needs time-based detection |
| RULE-022 (read-only indices) | ❌ | ✅ (flood stage) | ✅ |
| RULE-023 (CPU saturation) | ❌ | ⚠️ (128 MB heap → GC CPU) | ✅ |
| RULE-024 (stuck ILM) | ❌ | ❌ | ⚠️ needs time-based detection |

**Coverage summary:** 18/24 rules directly testable against the current broken fixture. 6 rules (RULE-010, RULE-016, RULE-017, RULE-018, RULE-021, RULE-024) require extended fixtures or time-delayed checks.

### Recommended Fixture Extensions

| Rule(s) | Extension needed |
|---------|-----------------|
| RULE-010 (shard imbalance) | Add a second node to the broken fixture with different disk capacity |
| RULE-016 (node loss) | Multi-node broken fixture; stop one node after seeding |
| RULE-017 (mapping explosion) | Seed an index with 15000 dynamically mapped fields |
| RULE-018 (oversized shards) | Seed a single index with 10 GB of data |
| RULE-021 (ILM not applied) | Add an index created >7 days ago without ILM policy |
| RULE-024 (stuck ILM) | Create an index with an ILM policy where the rollover condition is impossible to meet |

---

## 4. Rule Configuration

Each rule reads from a shared config object to keep thresholds tunable without code changes.

```python
class RuleConfig(BaseModel):
    disk_high_watermark_threshold: float = 0.85      # triggers RULE-003
    disk_low_watermark_threshold: float = 0.90       # triggers RULE-004
    flood_stage_threshold: float = 0.95              # triggers RULE-005
    heap_warning_threshold: float = 0.75             # triggers RULE-007
    heap_critical_threshold: float = 0.90            # triggers RULE-006
    shard_density_threshold: int = 300               # triggers RULE-009
    thread_pool_queue_threshold: float = 0.9         # triggers RULE-012
    tiny_shard_doc_count_threshold: int = 1000       # triggers RULE-019
    mapping_field_threshold: int = 10000             # triggers RULE-017
    oversized_shard_bytes: int = 50 * 1024**3        # triggers RULE-018
    cpu_warning_threshold: float = 0.85              # triggers RULE-023
```

---

## 5. References

- SOP §5 — Cluster Doctor Implementation
- ADR-004 — Evidence-First Deterministic Cluster Doctor
- Component contract — `guardian/rules/` and `guardian/diagnosis/` modules
- `docs/architecture/data-model.md` — Finding, EvidenceRef, ClusterSnapshot, NodeSnapshot
