"""Unit tests for the Cluster Doctor rule engine.

Tests cover:
- Healthy fixture produces no findings
- Broken fixture triggers expected rules (RULE-003, RULE-006, RULE-008, RULE-011, RULE-012, RULE-023)
- Rule metadata (severity, confidence, safety_level)
- Evidence linking to snapshot fields
- Finding lifecycle (first_seen_at, last_seen_at, resolved_at)
"""

from datetime import datetime, timezone

import pytest

from guardian.diagnosis import DiagnosisEngine, DiagnosisResult
from guardian.models import (
    ClusterSnapshot,
    CollectionResult,
    FilesystemSnapshot,
    IndexSnapshot,
    JvmSnapshot,
    NodeSnapshot,
    OsSnapshot,
    ProcessSnapshot,
    ShardState,
    ThreadPoolSnapshot,
)
from guardian.rules import RuleConfig


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_collection_result(
    health: str = "green",
    node_snapshots: dict | None = None,
    shard_states: list | None = None,
    index_snapshots: dict | None = None,
    cluster_name: str = "test-cluster",
    snapshot_id: str = "snap-001",
) -> CollectionResult:
    cs = ClusterSnapshot(
        snapshot_id=snapshot_id,
        cluster_name=cluster_name,
        collected_at=datetime.now(timezone.utc),
        health_status=health,
        total_nodes=1,
        data_nodes=1,
        master_nodes=1,
        ingest_nodes=0,
        active_primary_shards=5,
        active_shards=5,
        relocating_shards=0,
        initializing_shards=0,
        unassigned_shards=0,
        pending_cluster_tasks=0,
        failed_cluster_tasks=0,
        source_version="2.17.1",
    )
    return CollectionResult(
        cluster_snapshot=cs,
        node_snapshots=node_snapshots or {},
        index_snapshots=index_snapshots or {},
        shard_states=shard_states or [],
        collected_at=datetime.now(timezone.utc),
    )


def _make_node(
    node_name: str = "node-1",
    heap_used_percent: int = 30,
    old_gc_count: int = 0,
    cpu_percent: float = 20.0,
    filesystem_available_percent: float = 50.0,
    thread_pools: dict | None = None,
) -> NodeSnapshot:
    return NodeSnapshot(
        node_id=f"id-{node_name}",
        node_name=node_name,
        host="localhost",
        ip="127.0.0.1",
        roles=["data", "master"],
        version="2.17.1",
        collected_at=datetime.now(timezone.utc),
        jvm=JvmSnapshot(
            mem_heap_used_bytes=int(heap_used_percent * 100_000_000),
            mem_heap_max_bytes=100_000_000,
            mem_heap_used_percent=heap_used_percent,
            mem_non_heap_used_bytes=50_000_000,
            gc_collectors_young_count=5,
            gc_collectors_young_time_ms=100,
            gc_collectors_old_count=old_gc_count,
            gc_collectors_old_time_ms=50,
            buffer_pools_direct_count=2,
            buffer_pools_direct_used_bytes=1_000_000,
            buffer_pools_mapped_count=1,
            buffer_pools_mapped_used_bytes=500_000,
            uptime_ms=60000,
        ),
        os=OsSnapshot(
            cpu_percent=cpu_percent,
            load_average_1m=1.0,
            load_average_5m=1.0,
            load_average_15m=1.0,
            mem_total_bytes=8_000_000_000,
            mem_used_bytes=4_000_000_000,
            mem_free_bytes=4_000_000_000,
            mem_free_percent=50,
            mem_used_percent=50,
        ),
        process=ProcessSnapshot(
            cpu_percent=cpu_percent,
            cpu_total_ms=500000,
            open_file_descriptors=500,
            max_file_descriptors=65536,
            mem_swap_used_bytes=0,
            mem_swap_max_bytes=0,
        ),
        thread_pools=thread_pools or {
            "write": ThreadPoolSnapshot(name="write", threads=8, queue=100, active=2, rejected=0, completed=1000, leaked=0),
            "search": ThreadPoolSnapshot(name="search", threads=16, queue=50, active=3, rejected=0, completed=5000, leaked=0),
        },
        filesystems=[
            FilesystemSnapshot(
                total_bytes=10_000_000_000,
                available_bytes=int(10_000_000_000 * filesystem_available_percent / 100),
                used_bytes=int(10_000_000_000 * (100 - filesystem_available_percent) / 100),
                available_percent=filesystem_available_percent,
                disk_reads=10000,
                disk_writes=20000,
                disk_total_size_bytes=10_000_000_000,
            )
        ],
        source_version="2.17.1",
    )


# ---------------------------------------------------------------------------
# Healthy cluster — should produce no findings
# ---------------------------------------------------------------------------

class TestHealthyCluster:
    def test_green_cluster_no_findings(self):
        result = _make_collection_result(health="green", node_snapshots={"n1": _make_node()})
        engine = DiagnosisEngine()
        diag = engine.diagnose(result)
        assert diag.findings == []
        assert diag.critical_count == 0
        assert diag.high_count == 0

    def test_yellow_cluster_produces_finding(self):
        result = _make_collection_result(health="yellow", node_snapshots={"n1": _make_node()})
        engine = DiagnosisEngine()
        diag = engine.diagnose(result)
        rule_ids = {f.rule_id for f in diag.findings}
        assert "RULE-001" in rule_ids

    def test_red_cluster_produces_critical_finding(self):
        result = _make_collection_result(health="red", node_snapshots={"n1": _make_node()})
        engine = DiagnosisEngine()
        diag = engine.diagnose(result)
        critical = [f for f in diag.findings if f.severity == "critical"]
        assert any(f.rule_id == "RULE-001" for f in critical)


# ---------------------------------------------------------------------------
# Disk watermark rules
# ---------------------------------------------------------------------------

class TestDiskWatermarkRule:
    def test_flood_stage_triggers_critical(self):
        result = _make_collection_result(
            node_snapshots={"n1": _make_node(filesystem_available_percent=3.0)}
        )
        engine = DiagnosisEngine()
        diag = engine.diagnose(result)
        rule_ids = {f.rule_id for f in diag.findings}
        assert "RULE-003" in rule_ids
        critical = [f for f in diag.findings if f.severity == "critical"]
        assert any("flood stage" in f.condition_description for f in critical)

    def test_high_watermark_triggers(self):
        result = _make_collection_result(
            node_snapshots={"n1": _make_node(filesystem_available_percent=12.0)}
        )
        engine = DiagnosisEngine()
        diag = engine.diagnose(result)
        rule_ids = {f.rule_id for f in diag.findings}
        assert "RULE-003" in rule_ids

    def test_low_watermark_triggers(self):
        result = _make_collection_result(
            node_snapshots={"n1": _make_node(filesystem_available_percent=8.0)}
        )
        engine = DiagnosisEngine()
        diag = engine.diagnose(result)
        rule_ids = {f.rule_id for f in diag.findings}
        assert "RULE-003" in rule_ids

    def test_healthy_disk_no_finding(self):
        result = _make_collection_result(
            node_snapshots={"n1": _make_node(filesystem_available_percent=50.0)}
        )
        engine = DiagnosisEngine()
        diag = engine.diagnose(result)
        rule_ids = {f.rule_id for f in diag.findings}
        assert "RULE-003" not in rule_ids


# ---------------------------------------------------------------------------
# JVM heap rules
# ---------------------------------------------------------------------------

class TestJvmHeapRule:
    def test_critical_heap_triggers(self):
        result = _make_collection_result(
            node_snapshots={"n1": _make_node(heap_used_percent=94)}
        )
        engine = DiagnosisEngine()
        diag = engine.diagnose(result)
        rule_ids = {f.rule_id for f in diag.findings}
        assert "RULE-006" in rule_ids
        critical_high = [f for f in diag.findings if f.rule_id == "RULE-006"]
        assert all(f.severity == "high" for f in critical_high)

    def test_warning_heap_triggers(self):
        result = _make_collection_result(
            node_snapshots={"n1": _make_node(heap_used_percent=80)}
        )
        engine = DiagnosisEngine()
        diag = engine.diagnose(result)
        rule_ids = {f.rule_id for f in diag.findings}
        assert "RULE-006" in rule_ids

    def test_healthy_heap_no_finding(self):
        result = _make_collection_result(
            node_snapshots={"n1": _make_node(heap_used_percent=30)}
        )
        engine = DiagnosisEngine()
        diag = engine.diagnose(result)
        rule_ids = {f.rule_id for f in diag.findings}
        assert "RULE-006" not in rule_ids


class TestJvmGcRule:
    def test_excessive_old_gc_triggers(self):
        result = _make_collection_result(
            node_snapshots={"n1": _make_node(old_gc_count=15)}
        )
        engine = DiagnosisEngine()
        diag = engine.diagnose(result)
        rule_ids = {f.rule_id for f in diag.findings}
        assert "RULE-008" in rule_ids

    def test_normal_gc_no_finding(self):
        result = _make_collection_result(
            node_snapshots={"n1": _make_node(old_gc_count=2)}
        )
        engine = DiagnosisEngine()
        diag = engine.diagnose(result)
        rule_ids = {f.rule_id for f in diag.findings}
        assert "RULE-008" not in rule_ids


# ---------------------------------------------------------------------------
# Thread-pool rules
# ---------------------------------------------------------------------------

class TestThreadPoolRejectionRule:
    def test_rejections_trigger_critical(self):
        pools = {
            "write": ThreadPoolSnapshot(name="write", threads=8, queue=100, active=8, rejected=5, completed=1000, leaked=0),
            "search": ThreadPoolSnapshot(name="search", threads=16, queue=50, active=3, rejected=0, completed=5000, leaked=0),
        }
        result = _make_collection_result(
            node_snapshots={"n1": _make_node(thread_pools=pools)}
        )
        engine = DiagnosisEngine()
        diag = engine.diagnose(result)
        rule_ids = {f.rule_id for f in diag.findings}
        assert "RULE-011" in rule_ids
        critical = [f for f in diag.findings if f.severity == "critical"]
        assert any("rejections" in f.condition_description for f in critical)

    def test_no_rejections_no_finding(self):
        result = _make_collection_result(
            node_snapshots={"n1": _make_node()}
        )
        engine = DiagnosisEngine()
        diag = engine.diagnose(result)
        rule_ids = {f.rule_id for f in diag.findings}
        assert "RULE-011" not in rule_ids


class TestThreadPoolQueueRule:
    def test_queue_nearing_capacity_triggers(self):
        pools = {
            "write": ThreadPoolSnapshot(name="write", threads=8, queue=100, active=8, rejected=0, completed=1000, leaked=0),
        }
        result = _make_collection_result(
            node_snapshots={"n1": _make_node(thread_pools=pools)}
        )
        engine = DiagnosisEngine()
        diag = engine.diagnose(result)
        rule_ids = {f.rule_id for f in diag.findings}
        assert "RULE-012" in rule_ids

    def test_normal_queue_no_finding(self):
        result = _make_collection_result(
            node_snapshots={"n1": _make_node()}
        )
        engine = DiagnosisEngine()
        diag = engine.diagnose(result)
        rule_ids = {f.rule_id for f in diag.findings}
        assert "RULE-012" not in rule_ids


# ---------------------------------------------------------------------------
# CPU saturation rule
# ---------------------------------------------------------------------------

class TestCpuSaturationRule:
    def test_high_cpu_triggers(self):
        result = _make_collection_result(
            node_snapshots={"n1": _make_node(cpu_percent=92.5)}
        )
        engine = DiagnosisEngine()
        diag = engine.diagnose(result)
        rule_ids = {f.rule_id for f in diag.findings}
        assert "RULE-023" in rule_ids

    def test_normal_cpu_no_finding(self):
        result = _make_collection_result(
            node_snapshots={"n1": _make_node(cpu_percent=30.0)}
        )
        engine = DiagnosisEngine()
        diag = engine.diagnose(result)
        rule_ids = {f.rule_id for f in diag.findings}
        assert "RULE-023" not in rule_ids


# ---------------------------------------------------------------------------
# Unassigned shard rules
# ---------------------------------------------------------------------------

class TestUnassignedShardsRule:
    def test_unassigned_primary_triggers_critical(self):
        shards = [
            ShardState(
                shard_id="0",
                index_name="logs-app-1",
                primary=True,
                state="UNASSIGNED",
                allocation_explanation="none",
                collected_at=datetime.now(timezone.utc),
            )
        ]
        result = _make_collection_result(shard_states=shards)
        engine = DiagnosisEngine()
        diag = engine.diagnose(result)
        critical = [f for f in diag.findings if f.severity == "critical"]
        assert any(f.rule_id == "RULE-013" for f in critical)

    def test_unassigned_replica_triggers_medium(self):
        shards = [
            ShardState(
                shard_id="0",
                index_name="logs-app-1",
                primary=False,
                state="UNASSIGNED",
                collected_at=datetime.now(timezone.utc),
            )
        ]
        result = _make_collection_result(shard_states=shards)
        engine = DiagnosisEngine()
        diag = engine.diagnose(result)
        medium = [f for f in diag.findings if f.severity == "medium"]
        assert any(f.rule_id == "RULE-014" for f in medium)

    def test_no_unassigned_shards_no_finding(self):
        shards = [
            ShardState(
                shard_id="0",
                index_name="logs-app-1",
                primary=True,
                state="STARTED",
                node_id="n1",
                collected_at=datetime.now(timezone.utc),
            )
        ]
        result = _make_collection_result(shard_states=shards)
        engine = DiagnosisEngine()
        diag = engine.diagnose(result)
        rule_ids = {f.rule_id for f in diag.findings}
        assert "RULE-013" not in rule_ids


# ---------------------------------------------------------------------------
# Read-only index rule
# ---------------------------------------------------------------------------

class TestReadOnlyIndexRule:
    def test_readonly_indices_trigger_finding(self):
        indices = {
            "logs-app-1": IndexSnapshot(
                index_name="logs-app-1",
                uuid="abc123",
                collected_at=datetime.now(timezone.utc),
                doc_count=1000,
                deleted_doc_count=0,
                store_size_bytes=5_000_000,
                primary_size_bytes=3_000_000,
                number_of_shards=5,
                number_of_replicas=0,
                total_shards=5,
                search_query_total=100,
                search_query_time_ms=5000,
                indexing_index_total=500,
                indexing_index_time_ms=10000,
                segment_count=10,
                segment_memory_bytes=1_000_000,
                refresh_interval_ms=1000,
                codec="default",
                lifecycle_policy=None,
                read_only=True,
                read_only_allow_delete=False,
                field_count=25,
                has_keyword_explosion=False,
                source_version="2.17.1",
            )
        }
        result = _make_collection_result(index_snapshots=indices)
        engine = DiagnosisEngine()
        diag = engine.diagnose(result)
        rule_ids = {f.rule_id for f in diag.findings}
        assert "RULE-022" in rule_ids

    def test_no_readonly_indices_no_finding(self):
        indices = {
            "logs-app-1": IndexSnapshot(
                index_name="logs-app-1",
                uuid="abc123",
                collected_at=datetime.now(timezone.utc),
                doc_count=1000,
                deleted_doc_count=0,
                store_size_bytes=5_000_000,
                primary_size_bytes=3_000_000,
                number_of_shards=5,
                number_of_replicas=0,
                total_shards=5,
                search_query_total=100,
                search_query_time_ms=5000,
                indexing_index_total=500,
                indexing_index_time_ms=10000,
                segment_count=10,
                segment_memory_bytes=1_000_000,
                refresh_interval_ms=1000,
                codec="default",
                lifecycle_policy=None,
                read_only=False,
                read_only_allow_delete=False,
                field_count=25,
                has_keyword_explosion=False,
                source_version="2.17.1",
            )
        }
        result = _make_collection_result(index_snapshots=indices)
        engine = DiagnosisEngine()
        diag = engine.diagnose(result)
        rule_ids = {f.rule_id for f in diag.findings}
        assert "RULE-022" not in rule_ids


# ---------------------------------------------------------------------------
# Evidence and finding structure
# ---------------------------------------------------------------------------

class TestEvidenceAndFindings:
    def test_finding_has_evidence(self):
        result = _make_collection_result(
            health="red",
            node_snapshots={"n1": _make_node(heap_used_percent=94, old_gc_count=15)},
        )
        engine = DiagnosisEngine()
        diag = engine.diagnose(result)
        findings = [f for f in diag.findings if f.rule_id == "RULE-001"]
        assert len(findings) == 1
        assert findings[0].evidence
        assert findings[0].evidence[0].source_api == "_cluster/health"
        assert findings[0].evidence[0].field_path == "status"
        assert findings[0].evidence[0].observed_value == "red"

    def test_finding_has_required_fields(self):
        result = _make_collection_result(
            health="red",
            node_snapshots={"n1": _make_node()},
        )
        engine = DiagnosisEngine()
        diag = engine.diagnose(result)
        findings = [f for f in diag.findings if f.rule_id == "RULE-001"]
        assert len(findings) == 1
        f = findings[0]
        assert f.rule_id == "RULE-001"
        assert f.rule_name
        assert f.severity == "critical"
        assert 0.0 <= f.confidence <= 1.0
        assert f.entity_type == "cluster"
        assert f.remediation_guidance
        assert f.safety_level == "informational"
        assert f.first_seen_at <= f.last_seen_at
        assert f.snapshot_id

    def test_finding_severity_ordering(self):
        result = _make_collection_result(
            health="red",
            node_snapshots={"n1": _make_node(heap_used_percent=94, old_gc_count=15)},
        )
        engine = DiagnosisEngine()
        diag = engine.diagnose(result)
        severities = [f.severity for f in diag.findings]
        assert "critical" in severities
        assert "high" in severities


# ---------------------------------------------------------------------------
# DiagnosisResult helpers
# ---------------------------------------------------------------------------

class TestDiagnosisResult:
    def test_by_severity(self):
        findings = [
            pytest.importorskip("guardian.rules").Finding(
                rule_id="RULE-001", rule_name="test", severity="critical",
                confidence=0.98, entity_type="cluster", entity_id="c1",
                observed_value="red", threshold_or_expected="green",
                condition_description="test", remediation_guidance="fix",
                safety_level="informational",
                first_seen_at=datetime.now(timezone.utc),
                last_seen_at=datetime.now(timezone.utc),
                snapshot_id="snap-1",
            ),
            pytest.importorskip("guardian.rules").Finding(
                rule_id="RULE-006", rule_name="test2", severity="high",
                confidence=0.96, entity_type="node", entity_id="n1",
                observed_value="94%", threshold_or_expected="<90%",
                condition_description="test", remediation_guidance="fix",
                safety_level="approval_required",
                first_seen_at=datetime.now(timezone.utc),
                last_seen_at=datetime.now(timezone.utc),
                snapshot_id="snap-1",
            ),
        ]
        result = DiagnosisResult(findings=findings, snapshot_id="snap-1", analyzed_at=datetime.now(timezone.utc))
        by_sev = result.by_severity()
        assert len(by_sev["critical"]) == 1
        assert len(by_sev["high"]) == 1
        assert result.critical_count == 1
        assert result.high_count == 1


# ---------------------------------------------------------------------------
# RuleConfig threshold overrides
# ---------------------------------------------------------------------------

class TestRuleConfigOverrides:
    def test_custom_thresholds(self):
        config = RuleConfig(heap_critical_threshold=0.50)
        engine = DiagnosisEngine(config=config)
        result = _make_collection_result(
            node_snapshots={"n1": _make_node(heap_used_percent=60)}
        )
        diag = engine.diagnose(result)
        rule_ids = {f.rule_id for f in diag.findings}
        assert "RULE-006" in rule_ids

    def test_higher_disk_threshold(self):
        config = RuleConfig(flood_stage_threshold=0.99)
        engine = DiagnosisEngine(config=config)
        result = _make_collection_result(
            node_snapshots={"n1": _make_node(filesystem_available_percent=3.0)}
        )
        diag = engine.diagnose(result)
        rule_ids = {f.rule_id for f in diag.findings}
        assert "RULE-003" in rule_ids  # still hits high watermark
