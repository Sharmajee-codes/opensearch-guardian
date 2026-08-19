"""Unit tests for Safety Classification system.

Tests SOP §8 4-tier classification and the classify_operation function.
"""

import pytest
from guardian.safety.classification import (
    SafetyClassification,
    classify_operation,
    OperationContext,
)


class TestSafetyClassification:
    """Tests for SafetyClassification enum values and properties."""

    def test_enum_values(self):
        assert SafetyClassification.INFORMATIONAL.value == "informational"
        assert SafetyClassification.SAFE_REVERSIBLE.value == "safe_reversible"
        assert SafetyClassification.APPROVAL_REQUIRED.value == "approval_required"
        assert SafetyClassification.DESTRUCTIVE.value == "destructive"

    def test_enum_membership(self):
        assert "informational" in {c.value for c in SafetyClassification}
        assert "safe_reversible" in {c.value for c in SafetyClassification}
        assert "approval_required" in {c.value for c in SafetyClassification}
        assert "destructive" in {c.value for c in SafetyClassification}


class TestClassifyOperation:
    """Tests for the classify_operation function per SOP §8."""

    def test_read_only_operation_is_informational(self):
        ctx = OperationContext(
            operation_type="cluster-health",
            target_resource="cluster",
            resource_type="cluster",
            parameters={},
            connection_permissions=["monitoring"],
            is_write_enabled=False,
        )
        assert classify_operation(ctx) == SafetyClassification.INFORMATIONAL

    def test_read_write_safe_operation(self):
        ctx = OperationContext(
            operation_type="index-create",
            target_resource="test-index",
            resource_type="index",
            parameters={"settings": {"number_of_shards": 3}},
            connection_permissions=["monitoring", "full"],
            is_write_enabled=True,
        )
        assert classify_operation(ctx) == SafetyClassification.SAFE_REVERSIBLE

    def test_write_without_full_permissions_requires_approval(self):
        ctx = OperationContext(
            operation_type="index-create",
            target_resource="test-index",
            resource_type="index",
            parameters={},
            connection_permissions=["monitoring"],
            is_write_enabled=False,
        )
        assert classify_operation(ctx) == SafetyClassification.APPROVAL_REQUIRED

    def test_destructive_operation_is_always_destructive(self):
        ctx = OperationContext(
            operation_type="index-delete",
            target_resource="test-index",
            resource_type="index",
            parameters={},
            connection_permissions=["monitoring", "full"],
            is_write_enabled=True,
        )
        assert classify_operation(ctx) == SafetyClassification.DESTRUCTIVE

    def test_cluster_shutdown_is_destructive(self):
        ctx = OperationContext(
            operation_type="cluster-shutdown",
            target_resource="cluster",
            resource_type="cluster",
            parameters={},
            connection_permissions=["monitoring", "full"],
            is_write_enabled=True,
        )
        assert classify_operation(ctx) == SafetyClassification.DESTRUCTIVE

    def test_provisioning_with_permissions_is_safe_reversible(self):
        ctx = OperationContext(
            operation_type="docker-compose-up",
            target_resource="opensearch-cluster",
            resource_type="docker",
            parameters={},
            connection_permissions=["monitoring", "full"],
            is_write_enabled=True,
        )
        assert classify_operation(ctx) == SafetyClassification.SAFE_REVERSIBLE

    def test_provisioning_without_permissions_requires_approval(self):
        ctx = OperationContext(
            operation_type="docker-compose-up",
            target_resource="opensearch-cluster",
            resource_type="docker",
            parameters={},
            connection_permissions=["monitoring"],
            is_write_enabled=False,
        )
        assert classify_operation(ctx) == SafetyClassification.APPROVAL_REQUIRED

    def test_unknown_write_operation_defaults_to_safe_reversible(self):
        ctx = OperationContext(
            operation_type="custom-operation",
            target_resource="resource",
            resource_type="custom",
            parameters={},
            connection_permissions=["full"],
            is_write_enabled=True,
        )
        assert classify_operation(ctx) == SafetyClassification.SAFE_REVERSIBLE

    def test_unknown_read_operation_defaults_to_informational(self):
        ctx = OperationContext(
            operation_type="custom-operation",
            target_resource="resource",
            resource_type="custom",
            parameters={},
            connection_permissions=["monitoring"],
            is_write_enabled=False,
        )
        assert classify_operation(ctx) == SafetyClassification.INFORMATIONAL

    def test_data_purge_is_destructive(self):
        ctx = OperationContext(
            operation_type="data-purge",
            target_resource="cluster",
            resource_type="cluster",
            parameters={},
            connection_permissions=["full"],
            is_write_enabled=True,
        )
        assert classify_operation(ctx) == SafetyClassification.DESTRUCTIVE

    def test_forced_merge_expunge_is_destructive(self):
        ctx = OperationContext(
            operation_type="forced-merge-expunge",
            target_resource="index",
            resource_type="index",
            parameters={},
            connection_permissions=["full"],
            is_write_enabled=True,
        )
        assert classify_operation(ctx) == SafetyClassification.DESTRUCTIVE

    def test_snapshot_delete_is_destructive(self):
        ctx = OperationContext(
            operation_type="snapshot-delete",
            target_resource="backup-snap",
            resource_type="snapshot",
            parameters={},
            connection_permissions=["full"],
            is_write_enabled=True,
        )
        assert classify_operation(ctx) == SafetyClassification.DESTRUCTIVE

    def test_snapshot_create_is_safe_reversible(self):
        ctx = OperationContext(
            operation_type="snapshot-create",
            target_resource="backup-snap",
            resource_type="snapshot",
            parameters={},
            connection_permissions=["full"],
            is_write_enabled=True,
        )
        assert classify_operation(ctx) == SafetyClassification.SAFE_REVERSIBLE

    def test_k8s_scale_down_is_safe_reversible_with_permissions(self):
        ctx = OperationContext(
            operation_type="k8s-scale",
            target_resource="opensearch-pool",
            resource_type="kubernetes",
            parameters={"replicas": 3},
            connection_permissions=["full"],
            is_write_enabled=True,
        )
        assert classify_operation(ctx) == SafetyClassification.SAFE_REVERSIBLE

    def test_node_delete_is_destructive(self):
        ctx = OperationContext(
            operation_type="node-delete",
            target_resource="node-1",
            resource_type="node",
            parameters={},
            connection_permissions=["full"],
            is_write_enabled=True,
        )
        assert classify_operation(ctx) == SafetyClassification.DESTRUCTIVE

    def test_pvc_delete_is_destructive(self):
        ctx = OperationContext(
            operation_type="pvc-delete",
            target_resource="pvc-data",
            resource_type="storage",
            parameters={},
            connection_permissions=["full"],
            is_write_enabled=True,
        )
        assert classify_operation(ctx) == SafetyClassification.DESTRUCTIVE


class TestOperationContext:
    """Tests for the OperationContext dataclass."""

    def test_defaults(self):
        ctx = OperationContext(
            operation_type="test",
            target_resource="res",
            resource_type="type",
            parameters={},
            connection_permissions=["monitoring"],
        )
        assert ctx.is_write_enabled is False

    def test_equality(self):
        ctx1 = OperationContext(
            operation_type="cluster-health",
            target_resource="c",
            resource_type="cluster",
            parameters={},
            connection_permissions=["monitoring"],
        )
        ctx2 = OperationContext(
            operation_type="cluster-health",
            target_resource="c",
            resource_type="cluster",
            parameters={},
            connection_permissions=["monitoring"],
        )
        assert ctx1 == ctx2

    def test_inequality_different_permissions(self):
        ctx1 = OperationContext(
            operation_type="test",
            target_resource="r",
            resource_type="t",
            parameters={},
            connection_permissions=["monitoring"],
        )
        ctx2 = OperationContext(
            operation_type="test",
            target_resource="r",
            resource_type="t",
            parameters={},
            connection_permissions=["full"],
        )
        assert ctx1 != ctx2
