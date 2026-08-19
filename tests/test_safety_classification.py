"""
Unit tests for the Security & Safety Engine classification module.
Tests the 4-tier operation classification system.
"""

import pytest
from guardian.safety.classification import (
    SafetyClassification,
    OperationContext,
    classify_operation,
)


class TestSafetyClassification:
    """Tests for SafetyClassification enum."""

    def test_classification_values(self):
        """Test that classification values are correct."""
        assert SafetyClassification.INFORMATIONAL.value == "informational"
        assert SafetyClassification.SAFE_REVERSIBLE.value == "safe_reversible"
        assert SafetyClassification.APPROVAL_REQUIRED.value == "approval_required"
        assert SafetyClassification.DESTRUCTIVE.value == "destructive"

    def test_classification_iteration(self):
        """Test iteration over classifications."""
        classifications = list(SafetyClassification)
        assert len(classifications) == 4


class TestOperationContext:
    """Tests for OperationContext dataclass."""

    def test_context_creation(self):
        """Test OperationContext creation."""
        context = OperationContext(
            operation_type="index-create",
            target_resource="test-index",
            resource_type="index",
            parameters={"number_of_shards": 5},
            connection_permissions=["monitoring", "full"],
            is_write_enabled=True
        )
        assert context.operation_type == "index-create"
        assert context.target_resource == "test-index"
        assert context.is_write_enabled is True

    def test_context_defaults(self):
        """Test OperationContext default values."""
        context = OperationContext(
            operation_type="cluster-health",
            target_resource="cluster",
            resource_type="cluster",
            parameters={},
            connection_permissions=["monitoring"]
        )
        assert context.is_write_enabled is False


class TestClassifyOperation:
    """Tests for classify_operation function."""

    def test_read_only_connection(self):
        """Test classification for read-only connection."""
        context = OperationContext(
            operation_type="cluster-health",
            target_resource="cluster",
            resource_type="cluster",
            parameters={},
            connection_permissions=["monitoring"],
            is_write_enabled=False
        )
        assert classify_operation(context) == SafetyClassification.INFORMATIONAL

    def test_write_enabled_safe_operation(self):
        """Test classification for safe operations with write enabled."""
        context = OperationContext(
            operation_type="index-create",
            target_resource="test-index",
            resource_type="index",
            parameters={"number_of_shards": 5},
            connection_permissions=["monitoring", "full"],
            is_write_enabled=True
        )
        assert classify_operation(context) == SafetyClassification.SAFE_REVERSIBLE

    def test_write_enabled_approval_required_operation(self):
        """Test classification for operations requiring approval."""
        context = OperationContext(
            operation_type="node-add",
            target_resource="data-node-1",
            resource_type="node",
            parameters={"role": "data"},
            connection_permissions=["monitoring", "full"],
            is_write_enabled=True
        )
        assert classify_operation(context) == SafetyClassification.SAFE_REVERSIBLE

    def test_write_disabled_approval_required_operation(self):
        """Test classification when write is disabled."""
        context = OperationContext(
            operation_type="node-add",
            target_resource="data-node-1",
            resource_type="node",
            parameters={"role": "data"},
            connection_permissions=["monitoring", "full"],
            is_write_enabled=False
        )
        assert classify_operation(context) == SafetyClassification.APPROVAL_REQUIRED

    def test_destructive_operation_denied(self):
        """Test classification for destructive operations."""
        context = OperationContext(
            operation_type="index-delete",
            target_resource="test-index",
            resource_type="index",
            parameters={},
            connection_permissions=["monitoring", "full"],
            is_write_enabled=True
        )
        assert classify_operation(context) == SafetyClassification.DESTRUCTIVE

    def test_provisioning_safe_with_write(self):
        """Test provisioning operations with write enabled."""
        context = OperationContext(
            operation_type="docker-compose-up",
            target_resource="opensearch",
            resource_type="docker_service",
            parameters={"image": "opensearchproject/opensearch"},
            connection_permissions=["monitoring", "full"],
            is_write_enabled=True
        )
        assert classify_operation(context) == SafetyClassification.SAFE_REVERSIBLE

    def test_provisioning_requires_approval_without_write(self):
        """Test provisioning operations without write enabled."""
        context = OperationContext(
            operation_type="docker-compose-up",
            target_resource="opensearch",
            resource_type="docker_service",
            parameters={"image": "opensearchproject/opensearch"},
            connection_permissions=["monitoring"],
            is_write_enabled=False
        )
        assert classify_operation(context) == SafetyClassification.APPROVAL_REQUIRED

    def test_unknown_operation_safe_with_write(self):
        """Test unknown operations with write enabled."""
        context = OperationContext(
            operation_type="custom-operation",
            target_resource="custom-resource",
            resource_type="custom",
            parameters={},
            connection_permissions=["monitoring", "full"],
            is_write_enabled=True
        )
        # Unknown write operations default to safe reversible
        assert classify_operation(context) == SafetyClassification.SAFE_REVERSIBLE

    def test_unknown_operation_without_write(self):
        """Test unknown operations without write enabled."""
        context = OperationContext(
            operation_type="custom-operation",
            target_resource="custom-resource",
            resource_type="custom",
            parameters={},
            connection_permissions=["monitoring"],
            is_write_enabled=False
        )
        # Unknown read operations are informational
        assert classify_operation(context) == SafetyClassification.INFORMATIONAL

    def test_all_destructive_operations(self):
        """Test all destructive operation types."""
        destructive_ops = [
            "index-delete",
            "node-delete",
            "pvc-delete",
            "snapshot-delete",
            "cluster-shutdown",
            "data-purge",
            "forced-merge-expunge"
        ]

        for op in destructive_ops:
            context = OperationContext(
                operation_type=op,
                target_resource="target",
                resource_type="resource",
                parameters={},
                connection_permissions=["monitoring", "full"],
                is_write_enabled=True
            )
            assert classify_operation(context) == SafetyClassification.DESTRUCTIVE, \
                f"Expected {op} to be classified as destructive"

    def test_all_approval_required_operations(self):
        """Test approval-required operation types."""
        approval_ops = [
            "index-create",
            "index-update-settings",
            "node-add",
            "node-remove",
            "shard-relocate",
            "snapshot-create",
            "snapshot-restore",
            "template-put",
            "component-template-put"
        ]

        for op in approval_ops:
            # Without write enabled
            context = OperationContext(
                operation_type=op,
                target_resource="target",
                resource_type="resource",
                parameters={},
                connection_permissions=["monitoring", "full"],
                is_write_enabled=False
            )
            assert classify_operation(context) == SafetyClassification.APPROVAL_REQUIRED, \
                f"Expected {op} to require approval when write is disabled"

            # With write enabled
            context.is_write_enabled = True
            assert classify_operation(context) == SafetyClassification.SAFE_REVERSIBLE, \
                f"Expected {op} to be safe-reversible when write is enabled"
