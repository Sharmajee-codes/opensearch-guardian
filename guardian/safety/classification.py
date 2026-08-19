"""
Safety classification system for the Security & Safety Engine.
Implements the 4-tier safety classification: Informational, Safe-Reversible,
Approval-Required, Destructive.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, List


class SafetyClassification(Enum):
    """4-tier safety classification for operations."""
    INFORMATIONAL = "informational"
    SAFE_REVERSIBLE = "safe_reversible"
    APPROVAL_REQUIRED = "approval_required"
    DESTRUCTIVE = "destructive"


@dataclass
class OperationContext:
    """Context for operation classification."""
    operation_type: str
    target_resource: str
    resource_type: str
    parameters: Dict[str, Any]
    connection_permissions: List[str]  # e.g., ["monitoring", "full"]
    is_write_enabled: bool = False


def classify_operation(context: OperationContext) -> SafetyClassification:
    """
    Classify an operation according to SOP §8 and ADR-002.

    Returns the appropriate safety tier based on operation type,
    target resource, and connection state.
    """
    # Read-only operations are always informational
    if not context.is_write_enabled and context.connection_permissions == ["monitoring"]:
        return SafetyClassification.INFORMATIONAL

    # Destructive operations that are never allowed autonomously in V1
    destructive_ops = {
        "index-delete", "node-delete", "pvc-delete", "snapshot-delete",
        "cluster-shutdown", "data-purge", "forced-merge-expunge"
    }

    if context.operation_type in destructive_ops:
        return SafetyClassification.DESTRUCTIVE

    # Write operations that require approval
    write_ops = {
        "index-create", "index-update-settings", "node-add", "node-remove",
        "shard-relocate", "snapshot-create", "snapshot-restore",
        "template-put", "component-template-put"
    }

    if context.operation_type in write_ops:
        # If write access is not explicitly enabled, require approval
        if not context.is_write_enabled or "full" not in context.connection_permissions:
            return SafetyClassification.APPROVAL_REQUIRED
        return SafetyClassification.SAFE_REVERSIBLE

    # Provisioning operations (Docker/K8s)
    provisioning_ops = {
        "docker-compose-up", "docker-compose-down", "k8s-scale",
        "helm-upgrade", "helm-install"
    }

    if context.operation_type in provisioning_ops:
        if not context.is_write_enabled or "full" not in context.connection_permissions:
            return SafetyClassification.APPROVAL_REQUIRED
        return SafetyClassification.SAFE_REVERSIBLE

    # Default to safe reversible for unknown write operations
    if context.is_write_enabled:
        return SafetyClassification.SAFE_REVERSIBLE

    # Read operations are informational
    return SafetyClassification.INFORMATIONAL