# Security & Safety Engine
# 4-tier operation classification, read-only-default access control,
# dry-run/diff, immutable audit snapshots, destructive-op guardrails,
# OS keychain secrets

from .classification import (
    SafetyClassification,
    classify_operation,
    OperationContext,
)
from .policy_engine import PolicyEngine, OperationViolation
from .mutation_filter import MutationFilter, MutationRequest, MutationResult
from .dryrun_engine import DryRunEngine, DiffResult
from .audit_store import AuditStore, AuditEntry
from .keychain_proxy import KeychainProxy, SecretNotFoundError

__all__ = [
    "SafetyClassification",
    "classify_operation",
    "OperationContext",
    "PolicyEngine",
    "OperationViolation",
    "MutationFilter",
    "MutationRequest",
    "MutationResult",
    "DryRunEngine",
    "DiffResult",
    "AuditStore",
    "AuditEntry",
    "KeychainProxy",
    "SecretNotFoundError",
]
