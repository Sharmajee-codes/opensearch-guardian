"""
Mutation Filter for the Security & Safety Engine.
Checks submitted mutation requests against an allow-list and enforces
destructive operation guards.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .policy_engine import OperationContext, OperationViolation, PolicyEngine


class MutationDecision(Enum):
    """Mutation filter decisions."""
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_DRY_RUN = "require_dry_run"


@dataclass
class MutationRequest:
    """Request to perform a mutation operation."""
    operation_type: str
    target_resource: str
    resource_type: str
    parameters: dict[str, Any]
    connection_context: OperationContext


@dataclass
class MutationResult:
    """Result of mutation filtering."""
    decision: MutationDecision
    violations: list[OperationViolation]
    allowed: bool
    requires_dry_run: bool = False


class MutationFilter:
    """
    Mutation filter that checks requests against an allow-list and
    enforces destructive operation guards per SOP §8 and ADR-002.
    """

    def __init__(self):
        # Allow-listed mutation operations (safe to perform)
        self.allowlisted_operations = {
            # Informational/Safe operations
            "cluster-health", "cluster-stats", "node-stats", "index-stats",
            "search", "mget", "termvectors",

            # Safe-reversible operations (require write access)
            "index-create", "index-update-settings", "index-open", "index-close",
            "alias-add", "alias-remove", "alias-swap",
            "snapshot-create", "snapshot-restore",
            "node-add", "node-remove", "shard-relocate",
            "template-put", "component-template-put",
            "composable-index-template-put",

            # Provisioning operations
            "docker-compose-up", "docker-compose-down", "docker-compose-pull",
            "k8s-scale-up", "k8s-scale-down", "helm-install", "helm-upgrade",
            "helm-uninstall",

            # Index management (require approval for destructive)
            "index-delete", "index-force-merge", "index-cleanup-aliases",
            "index-shrink", "index-split", "index-reroute",

            # Snapshot management
            "snapshot-delete", "snapshot-create-repo",
            "snapshot-delete-repo",
        }

        # Operations that are never allowed (destructive guards)
        self.never_allowed_operations = {
            "cluster-shutdown", "data-purge", "forced-merge-expunge",
            "delete-all-indices", "delete-cluster-metadata"
        }

        # Operations that require dry-run/diff before execution
        self.dry_run_required_operations = {
            "index-delete", "index-update-settings", "index-close",
            "node-add", "node-remove", "shard-relocate",
            "snapshot-delete", "snapshot-restore",
            "docker-compose-up", "docker-compose-down",
            "k8s-scale-up", "k8s-scale-down", "helm-upgrade", "helm-install",
            "helm-uninstall"
        }

        self.policy_engine = PolicyEngine()

    def filter_mutation(self, request: MutationRequest) -> MutationResult:
        """
        Filter a mutation request against security policies.

        Returns a MutationResult indicating whether the operation is allowed,
        requires dry-run, or should be denied.
        """
        # Check if operation is never allowed
        if request.operation_type in self.never_allowed_operations:
            violations = [OperationViolation(
                violation_type="operation_never_allowed",
                message=f"Operation '{request.operation_type}' is never allowed in V1",
                required_action="This operation is prohibited by design",
                context=request.connection_context
            )]
            return MutationResult(
                decision=MutationDecision.DENY,
                violations=violations,
                allowed=False,
                requires_dry_run=False
            )

        # Check if operation is allow-listed
        if request.operation_type not in self.allowlisted_operations:
            violations = [OperationViolation(
                violation_type="operation_not_allowlisted",
                message=f"Operation '{request.operation_type}' is not in the allow-list",
                required_action="Add operation to allow-list or use approved alternative",
                context=request.connection_context
            )]
            return MutationResult(
                decision=MutationDecision.DENY,
                violations=violations,
                allowed=False,
                requires_dry_run=False
            )

        # Check if dry-run is required
        requires_dry_run = request.operation_type in self.dry_run_required_operations
        if requires_dry_run:
            return MutationResult(
                decision=MutationDecision.REQUIRE_DRY_RUN,
                violations=[],
                allowed=False,
                requires_dry_run=True
            )

        # Run policy engine validation for remaining operations
        violations = self.policy_engine.validate_operation(request.connection_context)
        if violations:
            return MutationResult(
                decision=MutationDecision.DENY,
                violations=violations,
                allowed=False,
                requires_dry_run=False
            )

        return MutationResult(
            decision=MutationDecision.ALLOW,
            violations=[],
            allowed=True,
            requires_dry_run=False
        )

    def is_operation_allowlisted(self, operation_type: str) -> bool:
        """Check if an operation is in the allow-list."""
        return operation_type in self.allowlisted_operations

    def requires_dry_run(self, operation_type: str) -> bool:
        """Check if an operation requires dry-run execution."""
        return operation_type in self.dry_run_required_operations