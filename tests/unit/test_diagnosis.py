"""Tests for DiagnosisEngine and DiagnosisResult."""

import pytest
from datetime import datetime, timezone

from guardian.diagnosis import DiagnosisEngine, DiagnosisResult
from guardian.models import CollectionResult, ClusterSnapshot
from guardian.rules import Finding, RuleConfig
from guardian.rules.base import EvidenceItem


class TestDiagnosisResult:
    """Tests for DiagnosisResult."""

    def test_findings_count(self):
        findings = [
            Finding(
                rule_id="rule1", rule_name="Rule 1", severity="critical",
                confidence=1.0, entity_type="cluster", entity_id="c1",
                observed_value=1, threshold_or_expected=0,
                condition_description="desc", remediation_guidance="fix",
                safety_level="safe",
            ),
            Finding(
                rule_id="rule2", rule_name="Rule 2", severity="high",
                confidence=0.9, entity_type="cluster", entity_id="c1",
                observed_value=1, threshold_or_expected=0,
                condition_description="desc", remediation_guidance="fix",
                safety_level="safe",
            ),
        ]
        result = DiagnosisResult(
            findings=findings,
            snapshot_id="snap-1",
            analyzed_at=datetime.now(timezone.utc),
        )
        assert len(result.findings) == 2
        assert result.snapshot_id == "snap-1"

    def test_critical_count(self):
        findings = [
            Finding(
                rule_id="r1", rule_name="R1", severity="critical",
                confidence=1.0, entity_type="cluster", entity_id="c1",
                observed_value=1, threshold_or_expected=0,
                condition_description="desc", remediation_guidance="fix",
                safety_level="safe",
            ),
            Finding(
                rule_id="r2", rule_name="R2", severity="critical",
                confidence=1.0, entity_type="cluster", entity_id="c1",
                observed_value=1, threshold_or_expected=0,
                condition_description="desc", remediation_guidance="fix",
                safety_level="safe",
            ),
            Finding(
                rule_id="r3", rule_name="R3", severity="high",
                confidence=0.9, entity_type="cluster", entity_id="c1",
                observed_value=1, threshold_or_expected=0,
                condition_description="desc", remediation_guidance="fix",
                safety_level="safe",
            ),
        ]
        result = DiagnosisResult(
            findings=findings,
            snapshot_id="snap-1",
            analyzed_at=datetime.now(timezone.utc),
        )
        assert result.critical_count == 2
        assert result.high_count == 1

    def test_by_severity_groups(self):
        findings = [
            Finding(
                rule_id="r1", rule_name="R1", severity="critical",
                confidence=1.0, entity_type="cluster", entity_id="c1",
                observed_value=1, threshold_or_expected=0,
                condition_description="desc", remediation_guidance="fix",
                safety_level="safe",
            ),
            Finding(
                rule_id="r2", rule_name="R2", severity="high",
                confidence=0.9, entity_type="cluster", entity_id="c1",
                observed_value=1, threshold_or_expected=0,
                condition_description="desc", remediation_guidance="fix",
                safety_level="safe",
            ),
        ]
        result = DiagnosisResult(
            findings=findings,
            snapshot_id="snap-1",
            analyzed_at=datetime.now(timezone.utc),
        )
        grouped = result.by_severity()
        assert len(grouped["critical"]) == 1
        assert len(grouped["high"]) == 1

    def test_empty_findings(self):
        result = DiagnosisResult(
            findings=[],
            snapshot_id="snap-1",
            analyzed_at=datetime.now(timezone.utc),
        )
        assert result.critical_count == 0
        assert result.high_count == 0
        assert result.by_severity() == {}


class TestDiagnosisEngine:
    """Tests for DiagnosisEngine."""

    def _make_snapshot(self):
        """Helper to create a minimal CollectionResult."""
        cluster_snapshot = ClusterSnapshot(
            snapshot_id="snap-1",
            cluster_name="test-cluster",
            collected_at=datetime.now(timezone.utc),
            health_status="green",
            total_nodes=3,
            data_nodes=3,
            master_nodes=1,
            ingest_nodes=0,
            active_primary_shards=5,
            active_shards=10,
            relocating_shards=0,
            initializing_shards=0,
            unassigned_shards=0,
            delayed_unassigned_shards=0,
            pending_cluster_tasks=0,
            failed_cluster_tasks=0,
            source_api="http://localhost:9200",
            source_version="2.17.1",
            raw_response_hash="abc123",
        )
        return CollectionResult(
            cluster_snapshot=cluster_snapshot,
            node_snapshots={},
            index_snapshots={},
            shard_states=[],
            collected_at=datetime.now(timezone.utc),
        )

    def test_diagnose_runs_all_rules(self):
        """Diagnosis should run all configured rules."""
        engine = DiagnosisEngine()
        snapshot = self._make_snapshot()
        result = engine.diagnose(snapshot)

        assert isinstance(result, DiagnosisResult)
        assert result.snapshot_id == "snap-1"

    def test_diagnose_with_config(self):
        """Diagnosis should respect custom config."""
        config = RuleConfig(flood_stage_threshold=0.5)
        engine = DiagnosisEngine(config=config)
        snapshot = self._make_snapshot()
        result = engine.diagnose(snapshot)

        assert isinstance(result, DiagnosisResult)

    def test_diagnose_with_none_snapshot(self):
        """Diagnosis should handle None cluster snapshot gracefully."""
        engine = DiagnosisEngine()
        snapshot = CollectionResult(
            cluster_snapshot=None,
            node_snapshots={},
            index_snapshots={},
            shard_states=[],
            collected_at=datetime.now(timezone.utc),
        )
        # Should not raise
        result = engine.diagnose(snapshot)
        assert isinstance(result, DiagnosisResult)

    def test_engine_rule_count(self):
        """Engine should have 11 rules configured."""
        engine = DiagnosisEngine()
        assert len(engine._rules) == 11

    def test_diagnose_returns_findings_list(self):
        """Diagnosis should return findings as a list."""
        engine = DiagnosisEngine()
        snapshot = self._make_snapshot()
        result = engine.diagnose(snapshot)
        assert isinstance(result.findings, list)
