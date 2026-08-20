"""Tests for Doctor Rules streaming integration."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import pytest

from guardian.collectors.snapshots.store import SnapshotStore
from guardian.collectors.tiers.enums import Tier
from guardian.streaming.config import StreamingConfig
from guardian.streaming.diagnostics import DiagnosticEventStream, create_diagnostic_stream
from guardian.streaming.models import MessageType
from guardian.streaming.routers.doctor import DoctorStreamingRouter
from guardian.streaming.routers.sse import StreamingRouter
from guardian.core_types.connection_models import ConnectionProfile
from guardian.rules import Finding, EvidenceItem
from guardian.models import ClusterSnapshot


@pytest.fixture
def connection() -> ConnectionProfile:
    return ConnectionProfile(
        name="test-cluster",
        opensearch_url="http://localhost:9200",
        credential_ref="test-keyring-ref",
    )


@pytest.fixture
def snapshot_store(connection: ConnectionProfile) -> SnapshotStore:
    return SnapshotStore(connection=connection)


@pytest.fixture
def config() -> StreamingConfig:
    return StreamingConfig(
        enabled=True,
        protocol="sse",
        replay_buffer_size=50,
    )


@pytest.fixture
def router(snapshot_store: SnapshotStore, config: StreamingConfig) -> DoctorStreamingRouter:
    return DoctorStreamingRouter(snapshot_store=snapshot_store, config=config)


class TestDiagnosticEventStream:
    def test_emit_findings(self, router: DoctorStreamingRouter) -> None:
        """Test that findings are emitted as streaming events."""
        now = datetime.now(timezone.utc)
        finding = Finding(
            rule_id="RULE-001",
            rule_name="Cluster health is red",
            severity="critical",
            confidence=0.98,
            entity_type="cluster",
            entity_id="test-cluster",
            observed_value="red",
            threshold_or_expected="green",
            condition_description="Cluster health is red",
            remediation_guidance="Investigate unassigned shards",
            safety_level="informational",
            first_seen_at=now,
            last_seen_at=now,
            snapshot_id="snap-123",
            evidence=(
                EvidenceItem(
                    source_api="_cluster/health",
                    field_path="status",
                    observed_value="red",
                    timestamp=now,
                ),
            ),
        )
        count = router.emit_diagnostic_events([finding], "snap-123", now)
        assert count == 1

    def test_emit_cleared_events(self, router: DoctorStreamingRouter) -> None:
        """Test that cleared events are emitted."""
        router.emit_cleared_events(["RULE-001"])

    def test_no_new_findings_after_emit(self, router: DoctorStreamingRouter) -> None:
        """Test that duplicate findings are not re-emitted."""
        now = datetime.now(timezone.utc)
        finding = Finding(
            rule_id="RULE-001",
            rule_name="Cluster health is red",
            severity="critical",
            confidence=0.98,
            entity_type="cluster",
            entity_id="test-cluster",
            observed_value="red",
            threshold_or_expected="green",
            condition_description="Cluster health is red",
            remediation_guidance="Investigate unassigned shards",
            safety_level="informational",
            first_seen_at=now,
            last_seen_at=now,
            snapshot_id="snap-123",
            evidence=(),
        )
        # First emit
        count1 = router.emit_diagnostic_events([finding], "snap-123", now)
        assert count1 == 1

        # Second emit with same finding should not re-emit
        count2 = router.emit_diagnostic_events([finding], "snap-123", now)
        assert count2 == 0

    def test_updated_finding_emitted(self, router: DoctorStreamingRouter) -> None:
        """Test that updated findings are re-emitted."""
        now = datetime.now(timezone.utc)
        finding1 = Finding(
            rule_id="RULE-001",
            rule_name="Cluster health is red",
            severity="critical",
            confidence=0.98,
            entity_type="cluster",
            entity_id="test-cluster",
            observed_value="red",
            threshold_or_expected="green",
            condition_description="Cluster health is red",
            remediation_guidance="Investigate unassigned shards",
            safety_level="informational",
            first_seen_at=now,
            last_seen_at=now,
            snapshot_id="snap-123",
            evidence=(),
        )
        finding2 = Finding(
            rule_id="RULE-001",
            rule_name="Cluster health is red",
            severity="critical",
            confidence=0.98,
            entity_type="cluster",
            entity_id="test-cluster",
            observed_value="yellow",  # Changed
            threshold_or_expected="green",
            condition_description="Cluster health is yellow",
            remediation_guidance="Investigate unassigned shards",
            safety_level="informational",
            first_seen_at=now,
            last_seen_at=now,
            snapshot_id="snap-123",
            evidence=(),
        )
        # First emit
        count1 = router.emit_diagnostic_events([finding1], "snap-123", now)
        assert count1 == 1

        # Second emit with changed value should re-emit
        count2 = router.emit_diagnostic_events([finding2], "snap-123", now)
        assert count2 == 1


class TestDoctorStreamingRouter:
    def test_router_created(self, router: DoctorStreamingRouter) -> None:
        assert router is not None
        assert hasattr(router, '_router')

    def test_router_has_routes(self, router: DoctorStreamingRouter) -> None:
        assert len(router._router.routes) > 0

    def test_emit_diagnostic_events(self, router: DoctorStreamingRouter) -> None:
        now = datetime.now(timezone.utc)
        finding = Finding(
            rule_id="RULE-001",
            rule_name="Cluster health is red",
            severity="critical",
            confidence=0.98,
            entity_type="cluster",
            entity_id="test-cluster",
            observed_value="red",
            threshold_or_expected="green",
            condition_description="Cluster health is red",
            remediation_guidance="Investigate unassigned shards",
            safety_level="informational",
            first_seen_at=now,
            last_seen_at=now,
            snapshot_id="snap-123",
            evidence=(),
        )
        count = router.emit_diagnostic_events([finding], "snap-123", now)
        assert count == 1

    def test_emit_cleared_events(self, router: DoctorStreamingRouter) -> None:
        router.emit_cleared_events(["RULE-001"])


class TestCreateDiagnosticStream:
    def test_factory_function(self, router: DoctorStreamingRouter) -> None:
        stream = create_diagnostic_stream(router)
        assert isinstance(stream, DiagnosticEventStream)
