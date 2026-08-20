# Security & Safety Engine
# 4-tier operation classification, read-only-default access control,
# dry-run/diff, immutable audit snapshots, destructive-op guardrails,
# OS keychain secrets

from .audit_store import AuditEntry, AuditStore
from .classification import (
    OperationContext,
    SafetyClassification,
    classify_operation,
)
from .dryrun_engine import DiffResult, DryRunEngine
from .keychain_proxy import KeychainProxy, SecretNotFoundError
from .mutation_filter import MutationFilter, MutationRequest, MutationResult
from .policy_engine import OperationViolation, PolicyEngine

__all__ = [
    "AuditEntry",
    "AuditStore",
    "DiffResult",
    "DryRunEngine",
    "KeychainProxy",
    "MutationFilter",
    "MutationRequest",
    "MutationResult",
    "OperationContext",
    "OperationViolation",
    "PolicyEngine",
    "SafetyClassification",
    "SecretNotFoundError",
    "classify_operation",
]
