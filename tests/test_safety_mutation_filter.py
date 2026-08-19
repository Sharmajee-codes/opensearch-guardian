"""
Unit tests for the Security & Safety Engine mutation filter.
Tests mutation request filtering and allow-list enforcement.
"""

import pytest
from guardian.safety.classification import OperationContext
from guardian.safety.mutation_filter import (
    MutationFilter,
    MutationRequest,
    MutationDecision,
)


class TestMutationFilter:
    """Tests for MutationFilter."""

    @pytest.fixture
    def filter_engine(self):
        return MutationFilter()

    def test_allowlisted_operations(self, filter_engine):
        """Test that allowlisted operations pass filtering."""
        allowlisted_ops = [
            "cluster-health",
            "cluster-stats",
            "index-create",
            "node-add",
            "snapshot-create",
            "docker-compose-up",
            "k8s-scale-up"
        ]

        for op in allowlisted_ops:
            request = MutationRequest(
                operation_type=op,
                target_resource="test-resource",
                resource_type="test",
                parameters={},
                connection_context=OperationContext(
                    operation_type=op,
                    target_resource="test-resource",
                    resource_type="test",
                    parameters={},
                    connection_permissions=["monitoring", "full"],
                    is_write_enabled=True
                )
            )
            result = filter_engine.filter_mutation(request)
            assert result.decision != MutationDecision.DENY, \
                f"Operation {op} should not be denied if allowlisted"

    def test_never_allowed_operations(self, filter_engine):
        """Test that never-allowed operations are denied."""
        never_allowed_ops = [
            "cluster-shutdown",
            "data-purge",
            "forced-merge-expunge",
            "delete-all-indices",
            "delete-cluster-metadata"
        ]

        for op in never_allowed_ops:
            request = MutationRequest(
                operation_type=op,
                target_resource="test-resource",
                resource_type="test",
                parameters={},
                connection_context=OperationContext(
                    operation_type=op,
                    target_resource="test-resource",
                    resource_type="test",
                    parameters={},
                    connection_permissions=["monitoring", "full"],
                    is_write_enabled=True
                )
            )
            result = filter_engine.filter_mutation(request)
            assert result.decision == MutationDecision.DENY
            assert result.allowed is False

    def test_unallowlisted_operations(self, filter_engine):
        """Test that unallowlisted operations are denied."""
        request = MutationRequest(
            operation_type="unknown-operation",
            target_resource="test-resource",
            resource_type="test",
            parameters={},
            connection_context=OperationContext(
                operation_type="unknown-operation",
                target_resource="test-resource",
                resource_type="test",
                parameters={},
                connection_permissions=["monitoring", "full"],
                is_write_enabled=True
            )
        )
        result = filter_engine.filter_mutation(request)
        assert result.decision == MutationDecision.DENY
        assert result.allowed is False

    def test_dry_run_required_operations(self, filter_engine):
        """Test that dry-run required operations are flagged."""
        dry_run_ops = [
            "index-delete",
            "node-add",
            "docker-compose-up",
            "k8s-scale-up"
        ]

        for op in dry_run_ops:
            request = MutationRequest(
                operation_type=op,
                target_resource="test-resource",
                resource_type="test",
                parameters={},
                connection_context=OperationContext(
                    operation_type=op,
                    target_resource="test-resource",
                    resource_type="test",
                    parameters={},
                    connection_permissions=["monitoring", "full"],
                    is_write_enabled=True
                )
            )
            result = filter_engine.filter_mutation(request)
            if result.allowed or result.decision == MutationDecision.REQUIRE_DRY_RUN:
                assert result.requires_dry_run is True
            assert filter_engine.requires_dry_run(op) is True

    def test_requires_dry_run_check(self, filter_engine):
        """Test the requires_dry_run convenience method."""
        assert filter_engine.requires_dry_run("index-delete") is True
        assert filter_engine.requires_dry_run("cluster-health") is False

    def test_is_operation_allowlisted(self, filter_engine):
        """Test the is_operation_allowlisted convenience method."""
        assert filter_engine.is_operation_allowlisted("index-create") is True
        assert filter_engine.is_operation_allowlisted("cluster-health") is True
        assert filter_engine.is_operation_allowlisted("unknown-op") is False

    def test_denied_mutation_has_violations(self, filter_engine):
        """Test that denied mutations include violations."""
        request = MutationRequest(
            operation_type="index-delete",
            target_resource="test-index",
            resource_type="index",
            parameters={},
            connection_context=OperationContext(
                operation_type="index-delete",
                target_resource="test-index",
                resource_type="index",
                parameters={},
                connection_permissions=["monitoring", "full"],
                is_write_enabled=True
            )
        )
        result = filter_engine.filter_mutation(request)
        assert result.decision == MutationDecision.DENY
        assert len(result.violations) > 0

    def test_write_disabled_rejects_write_operations(self, filter_engine):
        """Test that write operations are rejected when write is disabled."""
        request = MutationRequest(
            operation_type="index-create",
            target_resource="test-index",
            resource_type="index",
            parameters={},
            connection_context=OperationContext(
                operation_type="index-create",
                target_resource="test-index",
                resource_type="index",
                parameters={},
                connection_permissions=["monitoring"],
                is_write_enabled=False
            )
        )
        result = filter_engine.filter_mutation(request)
        assert result.decision == MutationDecision.DENY
        assert result.allowed is False
