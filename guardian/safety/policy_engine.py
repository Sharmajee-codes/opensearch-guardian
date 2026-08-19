"""
Policy Engine for the Security & Safety Engine.
Evaluates operation classification and enforces approval workflows.
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional
from .classification import SafetyClassification, OperationContext


class PolicyDecision(Enum):
    """Policy enforcement decisions."""
    ALLOW = "allow"
    REQUIRE_APPROVAL = "require_approval"
    DENY = "deny"


@dataclass
class OperationViolation:
    """Represents a policy violation."""
    violation_type: str
    message: str
    required_action: str
    context: OperationContext


class PolicyEngine:
    """
    Policy engine that enforces safety classifications and approval requirements.
    Implements the access control policies from SOP §8 and ADR-002.
    """

    def __init__(self):
        # Operations that are never allowed autonomously in V1
        self.never_allowed_ops = {
            "index-delete", "node-delete", "pvc-delete", "snapshot-delete",
            "cluster-shutdown", "data-purge", "forced-merge-expunge"
        }

        # Operations that require explicit approval even with write access
        self.approval_required_ops = {
            "index-delete", "node-delete", "pvc-delete", "snapshot-delete",
            "cluster-shutdown", "data-purge", "forced-merge-expunge",
            "docker-compose-down", "k8s-scale-down", "helm-uninstall"
        }

    def evaluate_operation(self, context: OperationContext) -> PolicyDecision:
        """
        Evaluate an operation against security policies.

        Returns the appropriate policy decision.
        """
        # Never allow destructive operations autonomously in V1
        if context.operation_type in self.never_allowed_ops:
            return PolicyDecision.DENY

        # Check if operation requires approval based on classification
        classification = classify_operation(context)

        if classification == SafetyClassification.APPROVAL_REQUIRED:
            return PolicyDecision.REQUIRE_APPROVAL
        elif classification == SafetyClassification.DESTRUCTIVE:
            return PolicyDecision.DENY
        else:
            return PolicyDecision.ALLOW

    def validate_operation(self, context: OperationContext) -> List[OperationViolation]:
        """
        Validate an operation and return any violations.

        Returns a list of violations (empty if valid).
        """
        violations = []
        decision = self.evaluate_operation(context)

        if decision == PolicyDecision.DENY:
            violations.append(OperationViolation(
                violation_type="operation_denied",
                message=f"Operation '{context.operation_type}' is not allowed",
                required_action="Contact administrator for manual intervention",
                context=context
            ))
        elif decision == PolicyDecision.REQUIRE_APPROVAL:
            violations.append(OperationViolation(
                violation_type="approval_required",
                message=f"Operation '{context.operation_type}' requires explicit approval",
                required_action="Obtain approval through the approval workflow",
                context=context
            ))

        # Check connection permissions
        if not context.is_write_enabled and any(
            op in ["index-create", "index-update", "node-add", "node-remove"]
            for op in [context.operation_type]
        ):
            violations.append(OperationViolation(
                violation_type="insufficient_permissions",
                message="Write access is not enabled for this connection",
                required_action="Enable write access via connection management",
                context=context
            ))

        return violations

    def is_operation_allowed(self, context: OperationContext) -> bool:
        """
        Check if an operation is allowed without requiring approval.

        Returns True if allowed, False otherwise.
        """
        return self.evaluate_operation(context) == PolicyDecision.ALLOW