"""Unit tests for PolicyEngine."""

import pytest
from guardian.safety.policy_engine import PolicyEngine, PolicyDecision, OperationViolation
from guardian.safety.classification import OperationContext


@pytest.fixture
def policy_engine():
    return PolicyEngine()


class TestPolicyEngineEvaluate:
    """Tests for evaluate_operation method."""

    def test_read_only_health_check_is_allowed(self, policy_engine):
        ctx = OperationContext(
            operation_type="cluster-health",
            target_resource="cluster",
            resource_type="cluster",
            parameters={},
            connection_permissions=["monitoring"],
            is_write_enabled=False,
        )
        assert policy_engine.evaluate_operation(ctx) == PolicyDecision.ALLOW

    def test_never_allowed_ops_are_denied(self, policy_engine):
        for op in ["index-delete", "node-delete", "pvc-delete", "snapshot-delete",
                    "cluster-shutdown", "data-purge", "forced-merge-expunge"]:
            ctx = OperationContext(
                operation_type=op,
                target_resource="res",
                resource_type="type",
                parameters={},
                connection_permissions=["full"],
                is_write_enabled=True,
            )
            assert policy_engine.evaluate_operation(ctx) == PolicyDecision.DENY, \
                f"Expected DENY for {op}"

    def test_approval_required_ops_require_approval(self, policy_engine):
        for op in ["docker-compose-down", "k8s-scale-down", "helm-uninstall"]:
            ctx = OperationContext(
                operation_type=op,
                target_resource="res",
                resource_type="type",
                parameters={},
                connection_permissions=["full"],
                is_write_enabled=True,
            )
            assert policy_engine.evaluate_operation(ctx) == PolicyDecision.REQUIRE_APPROVAL, \
                f"Expected REQUIRE_APPROVAL for {op}"

    def test_safe_write_ops_are_allowed(self, policy_engine):
        ctx = OperationContext(
            operation_type="index-create",
            target_resource="test-index",
            resource_type="index",
            parameters={"settings": {}},
            connection_permissions=["monitoring", "full"],
            is_write_enabled=True,
        )
        assert policy_engine.evaluate_operation(ctx) == PolicyDecision.ALLOW

    def test_snapshot_create_is_allowed(self, policy_engine):
        ctx = OperationContext(
            operation_type="snapshot-create",
            target_resource="backup",
            resource_type="snapshot",
            parameters={},
            connection_permissions=["monitoring", "full"],
            is_write_enabled=True,
        )
        assert policy_engine.evaluate_operation(ctx) == PolicyDecision.ALLOW


class TestPolicyEngineValidate:
    """Tests for validate_operation method."""

    def test_valid_read_operation_has_no_violations(self, policy_engine):
        ctx = OperationContext(
            operation_type="cluster-health",
            target_resource="cluster",
            resource_type="cluster",
            parameters={},
            connection_permissions=["monitoring"],
            is_write_enabled=False,
        )
        violations = policy_engine.validate_operation(ctx)
        assert violations == []

    def test_denied_operation_has_violations(self, policy_engine):
        ctx = OperationContext(
            operation_type="index-delete",
            target_resource="test-index",
            resource_type="index",
            parameters={},
            connection_permissions=["full"],
            is_write_enabled=True,
        )
        violations = policy_engine.validate_operation(ctx)
        assert len(violations) >= 1
        assert any(v.violation_type == "operation_denied" for v in violations)

    def test_insufficient_permissions_violation(self, policy_engine):
        ctx = OperationContext(
            operation_type="index-create",
            target_resource="test-index",
            resource_type="index",
            parameters={},
            connection_permissions=["monitoring"],
            is_write_enabled=False,
        )
        violations = policy_engine.validate_operation(ctx)
        assert any(v.violation_type == "insufficient_permissions" for v in violations)


class TestPolicyEngineIsAllowed:
    """Tests for is_operation_allowed method."""

    def test_read_only_is_allowed(self, policy_engine):
        ctx = OperationContext(
            operation_type="cluster-health",
            target_resource="cluster",
            resource_type="cluster",
            parameters={},
            connection_permissions=["monitoring"],
            is_write_enabled=False,
        )
        assert policy_engine.is_operation_allowed(ctx) is True

    def test_destructive_is_not_allowed(self, policy_engine):
        ctx = OperationContext(
            operation_type="index-delete",
            target_resource="test-index",
            resource_type="index",
            parameters={},
            connection_permissions=["full"],
            is_write_enabled=True,
        )
        assert policy_engine.is_operation_allowed(ctx) is False


class TestNeverAllowedOpsSet:
    """Tests for the never_allowed_ops set."""

    def test_contains_expected_ops(self, policy_engine):
        expected = {"index-delete", "node-delete", "pvc-delete", "snapshot-delete",
                    "cluster-shutdown", "data-purge", "forced-merge-expunge"}
        assert policy_engine.never_allowed_ops == expected
