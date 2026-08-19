"""Builtin Doctor rules for the OpenSearch Guardian Cluster Doctor."""

from __future__ import annotations

from datetime import datetime, timezone

from .. import EvidenceItem, Finding, Rule, RuleConfig


class ClusterHealthRule(Rule):
    rule_id = "RULE-001"
    rule_name = "Cluster health is red or yellow"
    severity = "critical"
    applies_to = "cluster"
    confidence = 0.98
    remediation = (
        "Investigate unassigned shards via _cluster/allocation/explain. "
        "Check node health and disk watermarks as root causes."
    )
    safety_level = "informational"

    def evaluate(self, snapshot, config: RuleConfig) -> list[Finding]:
        findings: list[Finding] = []
        now = datetime.now(tz=timezone.utc)
        cs = snapshot.cluster_snapshot
        if cs is None:
            return findings

        if cs.health_status == "red":
            findings.append(self._make_finding(
                entity_type="cluster",
                entity_id=cs.cluster_name,
                observed_value=cs.health_status,
                threshold_or_expected="green",
                condition_description=(
                    f"Cluster health is red; {cs.unassigned_shards} unassigned shards, "
                    f"{cs.failed_cluster_tasks} failed tasks"
                ),
                evidence=[
                    EvidenceItem(source_api="_cluster/health", field_path="status",
                                 observed_value="red", timestamp=now),
                    EvidenceItem(source_api="_cluster/health", field_path="unassigned_shards",
                                 observed_value=cs.unassigned_shards, timestamp=now),
                ],
                snapshot_id=cs.snapshot_id,
                now=now,
            ))
        elif cs.health_status == "yellow":
            findings.append(self._make_finding(
                entity_type="cluster",
                entity_id=cs.cluster_name,
                observed_value=cs.health_status,
                threshold_or_expected="green or red",
                condition_description=(
                    f"Cluster health is yellow; {cs.unassigned_shards} unassigned replica shards"
                ),
                evidence=[
                    EvidenceItem(source_api="_cluster/health", field_path="status",
                                 observed_value="yellow", timestamp=now),
                ],
                snapshot_id=cs.snapshot_id,
                now=now,
            ))
        return findings


class DiskWatermarkRule(Rule):
    rule_id = "RULE-003"
    rule_name = "Disk usage exceeds watermark thresholds"
    severity = "critical"
    applies_to = "node"
    confidence = 0.99
    remediation = (
        "Free disk space immediately. Move shards to healthier nodes via _cluster/reroute. "
        "Investigate index retention and delete expired indices."
    )
    safety_level = "approval_required"

    def evaluate(self, snapshot, config: RuleConfig) -> list[Finding]:
        findings: list[Finding] = []
        now = datetime.now(tz=timezone.utc)
        cs_id = snapshot.cluster_snapshot.snapshot_id if snapshot.cluster_snapshot else ""
        for ns in snapshot.node_snapshots.values():
            for fs in ns.filesystems:
                if fs.total_bytes <= 0:
                    continue
                used_fraction = 1.0 - (fs.available_bytes / fs.total_bytes)
                if used_fraction >= config.flood_stage_threshold:
                    findings.append(self._make_finding(
                        entity_type="node", entity_id=ns.node_name,
                        observed_value=f"{used_fraction:.1%} used",
                        threshold_or_expected=f"< {config.flood_stage_threshold * 100:.0f}%",
                        condition_description=(
                            f"Disk at flood stage on {ns.node_name}: "
                            f"{fs.available_percent:.1f}% available"
                        ),
                        evidence=[
                            EvidenceItem(source_api="_nodes/stats", field_path="fs.available_percent",
                                         observed_value=fs.available_percent, timestamp=now),
                        ],
                        snapshot_id=cs_id, now=now,
                    ))
                elif used_fraction >= config.disk_high_watermark_threshold:
                    findings.append(self._make_finding(
                        entity_type="node", entity_id=ns.node_name,
                        observed_value=f"{used_fraction:.1%} used",
                        threshold_or_expected=f"< {config.disk_high_watermark_threshold * 100:.0f}%",
                        condition_description=(
                            f"Disk above high watermark on {ns.node_name}: "
                            f"{fs.available_percent:.1f}% available"
                        ),
                        evidence=[
                            EvidenceItem(source_api="_nodes/stats", field_path="fs.available_percent",
                                         observed_value=fs.available_percent, timestamp=now),
                        ],
                        snapshot_id=cs_id, now=now,
                    ))
                elif used_fraction >= config.disk_low_watermark_threshold:
                    findings.append(self._make_finding(
                        entity_type="node", entity_id=ns.node_name,
                        observed_value=f"{used_fraction:.1%} used",
                        threshold_or_expected=f"< {config.disk_low_watermark_threshold * 100:.0f}%",
                        condition_description=(
                            f"Disk above low watermark on {ns.node_name}: "
                            f"{fs.available_percent:.1f}% available"
                        ),
                        evidence=[
                            EvidenceItem(source_api="_nodes/stats", field_path="fs.available_percent",
                                         observed_value=fs.available_percent, timestamp=now),
                        ],
                        snapshot_id=cs_id, now=now,
                    ))
        return findings


class JvmHeapRule(Rule):
    rule_id = "RULE-006"
    rule_name = "JVM heap usage critical or warning"
    severity = "high"
    applies_to = "node"
    confidence = 0.96
    remediation = (
        "Increase heap allocation (capped at 50% of physical RAM). Investigate "
        "large field data caches, aggressive query patterns, or heap-heavy aggregations."
    )
    safety_level = "approval_required"

    def evaluate(self, snapshot, config: RuleConfig) -> list[Finding]:
        findings: list[Finding] = []
        now = datetime.now(tz=timezone.utc)
        cs_id = snapshot.cluster_snapshot.snapshot_id if snapshot.cluster_snapshot else ""
        for ns in snapshot.node_snapshots.values():
            jvm = ns.jvm
            pct = jvm.mem_heap_used_percent / 100.0
            if pct >= config.heap_critical_threshold:
                findings.append(self._make_finding(
                    entity_type="node", entity_id=ns.node_name,
                    observed_value=f"{jvm.mem_heap_used_percent}% ({jvm.mem_heap_used_bytes} / {jvm.mem_heap_max_bytes} bytes)",
                    threshold_or_expected=f"< {config.heap_critical_threshold * 100}%",
                    condition_description=f"JVM heap critical on {ns.node_name}: {jvm.mem_heap_used_percent}% used",
                    evidence=[
                        EvidenceItem(source_api="_nodes/stats/jvm", field_path="mem.heap_used_percent",
                                     observed_value=jvm.mem_heap_used_percent, timestamp=now),
                    ],
                    snapshot_id=cs_id, now=now,
                ))
            elif pct >= config.heap_warning_threshold:
                findings.append(self._make_finding(
                    entity_type="node", entity_id=ns.node_name,
                    observed_value=f"{jvm.mem_heap_used_percent}%",
                    threshold_or_expected=f"< {config.heap_warning_threshold * 100}%",
                    condition_description=f"JVM heap above warning on {ns.node_name}: {jvm.mem_heap_used_percent}% used",
                    evidence=[
                        EvidenceItem(source_api="_nodes/stats/jvm", field_path="mem.heap_used_percent",
                                     observed_value=jvm.mem_heap_used_percent, timestamp=now),
                    ],
                    snapshot_id=cs_id, now=now,
                ))
        return findings


class JvmGcRule(Rule):
    rule_id = "RULE-008"
    rule_name = "Excessive old-gen GC activity"
    severity = "high"
    applies_to = "node"
    confidence = 0.92
    remediation = (
        "Old-gen GC thrashing indicates heap exhaustion. Immediate heap increase "
        "or shard redistribution needed. Prolonged GC pauses cause thread-pool rejections."
    )
    safety_level = "approval_required"

    def evaluate(self, snapshot, config: RuleConfig) -> list[Finding]:
        findings: list[Finding] = []
        now = datetime.now(tz=timezone.utc)
        cs_id = snapshot.cluster_snapshot.snapshot_id if snapshot.cluster_snapshot else ""
        gc_threshold = 10
        for ns in snapshot.node_snapshots.values():
            if ns.jvm.gc_collectors_old_count >= gc_threshold:
                findings.append(self._make_finding(
                    entity_type="node", entity_id=ns.node_name,
                    observed_value=ns.jvm.gc_collectors_old_count,
                    threshold_or_expected=f"< {gc_threshold}",
                    condition_description=(
                        f"Excessive old-gen GC on {ns.node_name}: "
                        f"{ns.jvm.gc_collectors_old_count} collections, "
                        f"{ns.jvm.gc_collectors_old_time_ms}ms total"
                    ),
                    evidence=[
                        EvidenceItem(source_api="_nodes/stats/jvm",
                                     field_path="gc.collectors.old.count",
                                     observed_value=ns.jvm.gc_collectors_old_count, timestamp=now),
                        EvidenceItem(source_api="_nodes/stats/jvm",
                                     field_path="gc.collectors.old.time_ms",
                                     observed_value=ns.jvm.gc_collectors_old_time_ms, timestamp=now),
                    ],
                    snapshot_id=cs_id, now=now,
                ))
        return findings


class ShardDensityRule(Rule):
    rule_id = "RULE-009"
    rule_name = "Shard density above threshold"
    severity = "high"
    applies_to = "node"
    confidence = 0.93
    remediation = (
        "High shard count inflates JVM heap and slows cluster state updates. "
        "Rollover small indices, merge segments, or increase shard count cap."
    )
    safety_level = "safe_reversible"

    def evaluate(self, snapshot, config: RuleConfig) -> list[Finding]:
        findings: list[Finding] = []
        now = datetime.now(tz=timezone.utc)
        cs_id = snapshot.cluster_snapshot.snapshot_id if snapshot.cluster_snapshot else ""
        cs = snapshot.cluster_snapshot
        if cs is None:
            return findings
        total_shards = cs.active_primary_shards + cs.active_shards
        num_data_nodes = max(cs.data_nodes, 1)
        shards_per_node = total_shards // num_data_nodes
        if shards_per_node >= config.shard_density_threshold:
            findings.append(self._make_finding(
                entity_type="node",
                entity_id=list(snapshot.node_snapshots.values())[0].node_name
                    if snapshot.node_snapshots else "unknown",
                observed_value=shards_per_node,
                threshold_or_expected=f"< {config.shard_density_threshold}",
                condition_description=(
                    f"High shard density: ~{shards_per_node} shards/node "
                    f"(cluster-wide {total_shards} shards across {num_data_nodes} data nodes)"
                ),
                evidence=[
                    EvidenceItem(source_api="_cluster/health", field_path="active_shards",
                                 observed_value=total_shards, timestamp=now),
                ],
                snapshot_id=cs_id, now=now,
            ))
        return findings


class ThreadPoolRejectionRule(Rule):
    rule_id = "RULE-011"
    rule_name = "Thread-pool rejections detected"
    severity = "critical"
    applies_to = "node"
    confidence = 0.99
    remediation = (
        "A thread pool is saturated. Identify which pool (write, search, management) "
        "and address the bottleneck. Write rejections often follow disk pressure; "
        "search rejections often follow heap pressure."
    )
    safety_level = "informational"

    def evaluate(self, snapshot, config: RuleConfig) -> list[Finding]:
        findings: list[Finding] = []
        now = datetime.now(tz=timezone.utc)
        cs_id = snapshot.cluster_snapshot.snapshot_id if snapshot.cluster_snapshot else ""
        for ns in snapshot.node_snapshots.values():
            for pool_name, pool in ns.thread_pools.items():
                if pool.rejected > 0:
                    findings.append(self._make_finding(
                        entity_type="node", entity_id=ns.node_name,
                        observed_value=f"{pool.rejected} rejections in '{pool_name}' pool",
                        threshold_or_expected="0",
                        condition_description=(
                            f"Thread-pool rejections on {ns.node_name} [{pool_name}]: "
                            f"{pool.rejected} rejected, {pool.active}/{pool.threads} active"
                        ),
                        evidence=[
                            EvidenceItem(source_api="_nodes/stats/thread_pool",
                                         field_path=f"thread_pool.{pool_name}.rejected",
                                         observed_value=pool.rejected, timestamp=now),
                            EvidenceItem(source_api="_nodes/stats/thread_pool",
                                         field_path=f"thread_pool.{pool_name}.active",
                                         observed_value=pool.active, timestamp=now),
                        ],
                        snapshot_id=cs_id, now=now,
                    ))
        return findings


class ThreadPoolQueueRule(Rule):
    rule_id = "RULE-012"
    rule_name = "Thread-pool queue near capacity"
    severity = "high"
    applies_to = "node"
    confidence = 0.94
    remediation = (
        "Thread pool near saturation. Queue rejections imminent. "
        "Investigate query complexity or indexing throughput."
    )
    safety_level = "safe_reversible"

    def evaluate(self, snapshot, config: RuleConfig) -> list[Finding]:
        findings: list[Finding] = []
        now = datetime.now(tz=timezone.utc)
        cs_id = snapshot.cluster_snapshot.snapshot_id if snapshot.cluster_snapshot else ""
        for ns in snapshot.node_snapshots.values():
            for pool_name, pool in ns.thread_pools.items():
                if pool.threads > 0 and (pool.active / pool.threads) >= config.thread_pool_queue_threshold:
                    findings.append(self._make_finding(
                        entity_type="node", entity_id=ns.node_name,
                        observed_value=f"{pool.active}/{pool.threads} threads active in '{pool_name}'",
                        threshold_or_expected=f"< {config.thread_pool_queue_threshold * 100:.0f}%",
                        condition_description=(
                            f"Thread-pool near capacity on {ns.node_name} [{pool_name}]: "
                            f"{pool.active}/{pool.threads} active, queue={pool.queue}"
                        ),
                        evidence=[
                            EvidenceItem(source_api="_nodes/stats/thread_pool",
                                         field_path=f"thread_pool.{pool_name}.active",
                                         observed_value=pool.active, timestamp=now),
                            EvidenceItem(source_api="_nodes/stats/thread_pool",
                                         field_path=f"thread_pool.{pool_name}.threads",
                                         observed_value=pool.threads, timestamp=now),
                        ],
                        snapshot_id=cs_id, now=now,
                    ))
        return findings


class UnassignedShardsRule(Rule):
    rule_id = "RULE-013"
    rule_name = "Unassigned primary shards"
    severity = "critical"
    applies_to = "shard"
    confidence = 0.98
    remediation = (
        "Primary shard is unassigned — this index is partially or fully unavailable. "
        "Use _cluster/allocation/explain for root cause. Common causes: disk watermark, "
        "node departure, incompatible shard size."
    )
    safety_level = "approval_required"

    def evaluate(self, snapshot, config: RuleConfig) -> list[Finding]:
        findings: list[Finding] = []
        now = datetime.now(tz=timezone.utc)
        cs_id = snapshot.cluster_snapshot.snapshot_id if snapshot.cluster_snapshot else ""
        for shard in snapshot.shard_states:
            if shard.state == "UNASSIGNED" and shard.primary:
                findings.append(self._make_finding(
                    entity_type="shard", entity_id=shard.shard_id,
                    observed_value="UNASSIGNED (primary)",
                    threshold_or_expected="STARTED",
                    condition_description=(
                        f"Unassigned primary shard on {shard.index_name} [{shard.shard_id}]"
                    ),
                    evidence=[
                        EvidenceItem(source_api="_cluster/state",
                                     field_path=f"shards[{shard.index_name}][{shard.shard_id}].state",
                                     observed_value="UNASSIGNED", timestamp=now),
                        EvidenceItem(source_api="_cluster/state",
                                     field_path=f"shards[{shard.index_name}][{shard.shard_id}].allocation_explanation",
                                     observed_value=shard.allocation_explanation or "none", timestamp=now),
                    ],
                    snapshot_id=cs_id, now=now,
                ))
        return findings


class UnassignedReplicaShardsRule(Rule):
    rule_id = "RULE-014"
    rule_name = "Unassigned replica shards"
    severity = "medium"
    applies_to = "shard"
    confidence = 0.96
    remediation = (
        "Replica shards are unassigned. Data is safe (primaries exist) but availability "
        "is reduced. Check disk watermarks and allocation filters."
    )
    safety_level = "informational"

    def evaluate(self, snapshot, config: RuleConfig) -> list[Finding]:
        findings: list[Finding] = []
        now = datetime.now(tz=timezone.utc)
        cs_id = snapshot.cluster_snapshot.snapshot_id if snapshot.cluster_snapshot else ""
        for shard in snapshot.shard_states:
            if shard.state == "UNASSIGNED" and not shard.primary:
                findings.append(self._make_finding(
                    entity_type="shard", entity_id=shard.shard_id,
                    observed_value="UNASSIGNED (replica)",
                    threshold_or_expected="STARTED",
                    condition_description=(
                        f"Unassigned replica shard on {shard.index_name} [{shard.shard_id}]"
                    ),
                    evidence=[
                        EvidenceItem(source_api="_cluster/state",
                                     field_path=f"shards[{shard.index_name}][{shard.shard_id}].state",
                                     observed_value="UNASSIGNED", timestamp=now),
                    ],
                    snapshot_id=cs_id, now=now,
                ))
        return findings


class ReadOnlyIndexRule(Rule):
    rule_id = "RULE-022"
    rule_name = "Read-only indices present"
    severity = "high"
    applies_to = "cluster"
    confidence = 0.98
    remediation = (
        "One or more indices are in read-only mode (often triggered by the "
        "flood-stage watermark). Investigate the cause before clearing the block."
    )
    safety_level = "approval_required"

    def evaluate(self, snapshot, config: RuleConfig) -> list[Finding]:
        findings: list[Finding] = []
        now = datetime.now(tz=timezone.utc)
        cs_id = snapshot.cluster_snapshot.snapshot_id if snapshot.cluster_snapshot else ""
        readonly_indices = [idx for idx in snapshot.index_snapshots.values() if idx.read_only]
        if readonly_indices:
            findings.append(self._make_finding(
                entity_type="cluster",
                entity_id=snapshot.cluster_snapshot.cluster_name if snapshot.cluster_snapshot else "unknown",
                observed_value=len(readonly_indices),
                threshold_or_expected="0",
                condition_description=(
                    f"{len(readonly_indices)} index(es) in read-only block: "
                    f"{', '.join(idx.index_name for idx in readonly_indices)}"
                ),
                evidence=[
                    EvidenceItem(source_api="_settings", field_path="index.blocks.read_only",
                                 observed_value=[idx.index_name for idx in readonly_indices],
                                 timestamp=now),
                ],
                snapshot_id=cs_id, now=now,
            ))
        return findings


class CpuSaturationRule(Rule):
    rule_id = "RULE-023"
    rule_name = "CPU saturation on data node"
    severity = "high"
    applies_to = "node"
    confidence = 0.88
    remediation = (
        "Node CPU is saturated. Search and indexing latency will increase. "
        "Consider adding nodes or reducing query concurrency."
    )
    safety_level = "informational"

    def evaluate(self, snapshot, config: RuleConfig) -> list[Finding]:
        findings: list[Finding] = []
        now = datetime.now(tz=timezone.utc)
        cs_id = snapshot.cluster_snapshot.snapshot_id if snapshot.cluster_snapshot else ""
        for ns in snapshot.node_snapshots.values():
            if ns.os.cpu_percent >= config.cpu_warning_threshold * 100:
                findings.append(self._make_finding(
                    entity_type="node", entity_id=ns.node_name,
                    observed_value=f"{ns.os.cpu_percent}%",
                    threshold_or_expected=f"< {config.cpu_warning_threshold * 100:.0f}%",
                    condition_description=f"CPU saturation on {ns.node_name}: {ns.os.cpu_percent}% used",
                    evidence=[
                        EvidenceItem(source_api="_nodes/stats/os", field_path="os.cpu.percent",
                                     observed_value=ns.os.cpu_percent, timestamp=now),
                    ],
                    snapshot_id=cs_id, now=now,
                ))
        return findings
