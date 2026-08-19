"""
Unit tests for the Security & Safety Engine policy engine.
Tests policy evaluation and enforcement.
"""

import pytest
from guardian.safety.classification import OperationContext
from guardian.safety.policy_engine import PolicyEngine, PolicyDecision, OperationViolation


class TestPolicyEngine:
    """Tests for PolicyEngine."""

    @pytest.fixture
    def engine(self):
        return PolicyEngine()

    def test_allow_read_operations(self, engine):
        """Test that read operations are allowed."""
        context = OperationContext(
            operation_type="cluster-health",
            target_resource="cluster",
            resource_type="cluster",
            parameters={},
            connection_permissions=["monitoring"],
            is_write_enabled=False
        )
        assert engine.evaluate_operation(context) == PolicyDecision.ALLOW

    def test_deny_destructive_operations(self, engine):
        """Test that destructive operations are denied."""
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
            assert engine.evaluate_operation(context) == PolicyDecision.DENY

    def test_require_approval_without_write(self, engine):
        """Test that write operations require approval without write enabled."""
        write_ops = [
            "index-create",
            "node-add",
            "docker-compose-up",
            "k8s-scale-up"
        ]

        for op in write_ops:
            context = OperationContext(
                operation_type=op,
                target_resource="target",
                resource_type="resource",
                parameters={},
                connection_permissions=["monitoring", "full"],
                is_write_enabled=False
            )
            assert engine.evaluate_operation(context) == PolicyDecision.REQUIRE_APPROVAL

    def test_allow_write_with_permissions(self, engine):
        """Test that write operations are allowed with proper permissions."""
        context = OperationContext(
            operation_type="index-create",
            target_resource="test-index",
            resource_type="index",
            parameters={},
            connection_permissions=["monitoring", "full"],
            is_write_enabled=True
        )
        assert engine.evaluate_operation(context) == PolicyDecision.ALLOW

    def test_validate_returns_violations_for_dangerous_ops(self, engine):
        """Test that validation returns violations for dangerous operations."""
        context = OperationContext(
            operation_type="index-delete",
            target_resource="test-index",
            resource_type="index",
            parameters={},
            connection_permissions=["monitoring", "full"],
            is_write_enabled=True
        )
        violations = engine.validate_operation(context)
        assert len(violations) > 0
        assert any(v.violation_type == "operation_denied" for v in violations)

    def test_validate_returns_violations_for_unapproved_write(self, engine):
        """Test that validation returns violations for unapproved write."""
        context = OperationContext(
            operation_type="index-create",
            target_resource="test-index",
            resource_type="index",
            parameters={},
            connection_permissions=["monitoring", "full"],
            is_write_enabled=False
        )
        violations = engine.validate_operation(context)
        assert len(violations) > 0

    def test_is_operation_allowed(self, engine):
        """Test the is_operation_allowed convenience method."""
        # Read operation
        read_context = OperationContext(
            operation_type="cluster-health",
            target_resource="cluster",
            resource_type="cluster",
            parameters={},
            connection_permissions=["monitoring"],
            is_write_enabled=False
        )
        assert engine.is_operation_allowed(read_context) is True

        # Destructive operation
        destructive_context = OperationContext(
            operation_type="index-delete",
            target_resource="test-index",
            resource_type="index",
            parameters={},
            connection_permissions=["monitoring", "full"],
            is_write_enabled=True
        )
        assert engine.is_operation_allowed(destructive_context) is False

        # Write operation without permission
        write_context = OperationContext(
            operation_type="index-create",
            target_resource="test-index",
            resource_type="index",
            parameters={},
            connection_permissions=["monitoring"],
            is_write_enabled=False
        )
        assert engine.is_operation_allowed(write_context) is False

    def test_violation_context_preserved(self, engine):
        """Test that violation objects preserve the operation context."""
        context = OperationContext(
            operation_type="index-delete",
            target_resource="test-index",
            resource_type="index",
            parameters={"force": True},
            connection_permissions=["monitoring", "full"],
            is_write_enabled=True
        )
        violations = engine.validate_operation(context)

        if violations:
            assert violations[0].context == context
            assert violations[0].context.operation_type == "index-delete"
            assert violations[0].context.target_resource == "test-index"
