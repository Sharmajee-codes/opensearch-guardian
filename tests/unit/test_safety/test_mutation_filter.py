"""Unit tests for MutationFilter."""

import pytest
from guardian.safety.mutation_filter import MutationFilter, MutationDecision
from guardian.safety.classification import OperationContext


@pytest.fixture
def mutation_filter():
    return MutationFilter()


class TestMutationDecision:
    """Tests for MutationDecision enum."""

    def test_enum_values(self):
        assert MutationDecision.ALLOW.value == "allow"
        assert MutationDecision.DENY.value == "deny"
        assert MutationDecision.REQUIRE_DRY_RUN.value == "require_dry_run"


class TestIsOperationAllowlisted:
    """Tests for is_operation_allowlisted method."""

    def test_health_check_is_allowlisted(self, mutation_filter):
        assert mutation_filter.is_operation_allowlisted("cluster-health") is True

    def test_index_create_is_allowlisted(self, mutation_filter):
        assert mutation_filter.is_operation_allowlisted("index-create") is True

    def test_snapshot_create_is_allowlisted(self, mutation_filter):
        assert mutation_filter.is_operation_allowlisted("snapshot-create") is True

    def test_docker_compose_up_is_allowlisted(self, mutation_filter):
        assert mutation_filter.is_operation_allowlisted("docker-compose-up") is True

    def test_unknown_operation_is_not_allowlisted(self, mutation_filter):
        assert mutation_filter.is_operation_allowlisted("unknown-op") is False

    def test_forbidden_operation_is_not_allowlisted(self, mutation_filter):
        assert mutation_filter.is_operation_allowlisted("cluster-shutdown") is False


class TestRequiresDryRun:
    """Tests for requires_dry_run method."""

    def test_index_delete_requires_dry_run(self, mutation_filter):
        assert mutation_filter.requires_dry_run("index-delete") is True

    def test_snapshot_delete_requires_dry_run(self, mutation_filter):
        assert mutation_filter.requires_dry_run("snapshot-delete") is True

    def test_docker_compose_up_requires_dry_run(self, mutation_filter):
        assert mutation_filter.requires_dry_run("docker-compose-up") is True

    def test_health_check_does_not_require_dry_run(self, mutation_filter):
        assert mutation_filter.requires_dry_run("cluster-health") is False


class TestFilterMutation:
    """Tests for filter_mutation method."""

    def test_read_only_health_check_is_allowed(self, mutation_filter):
        ctx = OperationContext(
            operation_type="cluster-health",
            target_resource="cluster",
            resource_type="cluster",
            parameters={},
            connection_permissions=["monitoring"],
            is_write_enabled=False,
        )
        request = MutationRequest(
            operation_type="cluster-health",
            target_resource="cluster",
            resource_type="cluster",
            parameters={},
            connection_context=ctx,
        )
        result = mutation_filter.filter_mutation(request)
        assert result.decision == MutationDecision.ALLOW
        assert result.allowed is True
        assert result.requires_dry_run is False
        assert result.violations == []

    def test_write_without_permissions_is_denied(self, mutation_filter):
        ctx = OperationContext(
            operation_type="index-create",
            target_resource="test-index",
            resource_type="index",
            parameters={},
            connection_permissions=["monitoring"],
            is_write_enabled=False,
        )
        request = MutationRequest(
            operation_type="index-create",
            target_resource="test-index",
            resource_type="index",
            parameters={},
            connection_context=ctx,
        )
        result = mutation_filter.filter_mutation(request)
        assert result.decision == MutationDecision.DENY
        assert result.allowed is False
        assert len(result.violations) > 0

    def test_never_allowed_operation_is_denied(self, mutation_filter):
        ctx = OperationContext(
            operation_type="cluster-shutdown",
            target_resource="cluster",
            resource_type="cluster",
            parameters={},
            connection_permissions=["full"],
            is_write_enabled=True,
        )
        request = MutationRequest(
            operation_type="cluster-shutdown",
            target_resource="cluster",
            resource_type="cluster",
            parameters={},
            connection_context=ctx,
        )
        result = mutation_filter.filter_mutation(request)
        assert result.decision == MutationDecision.DENY
        assert any(v.violation_type == "operation_never_allowed" for v in result.violations)

    def test_allowlisted_write_with_permissions_is_allowed(self, mutation_filter):
        ctx = OperationContext(
            operation_type="index-create",
            target_resource="test-index",
            resource_type="index",
            parameters={"settings": {}},
            connection_permissions=["monitoring", "full"],
            is_write_enabled=True,
        )
        request = MutationRequest(
            operation_type="index-create",
            target_resource="test-index",
            resource_type="index",
            parameters={"settings": {}},
            connection_context=ctx,
        )
        result = mutation_filter.filter_mutation(request)
        assert result.decision == MutationDecision.ALLOW
        assert result.allowed is True

    def test_dry_run_required_operation(self, mutation_filter):
        ctx = OperationContext(
            operation_type="index-delete",
            target_resource="test-index",
            resource_type="index",
            parameters={},
            connection_permissions=["monitoring", "full"],
            is_write_enabled=True,
        )
        request = MutationRequest(
            operation_type="index-delete",
            target_resource="test-index",
            resource_type="index",
            parameters={},
            connection_context=ctx,
        )
        result = mutation_filter.filter_mutation(request)
        assert result.decision == MutationDecision.REQUIRE_DRY_RUN
        assert result.allowed is False
        assert result.requires_dry_run is True
