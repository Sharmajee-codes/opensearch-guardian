"""
Test cases for validating safety classification and operation validation logic in OpenSearch plugin context.
Tests the correctness of safety engine, mutation filter, policy engine, dry-run engine, and audit store.
"""
import pytest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch
from guardian.safety import (
    SafetyClassification,
    OperationContext,
    classify_operation,
    OperationViolation,
    DryRunEngine,
    DiffResult,
    AuditStore,
    AuditEntry
)
from guardian.safety.policy_engine import PolicyEngine, PolicyDecision
from guardian.safety.mutation_filter import MutationFilter, MutationRequest, MutationDecision, MutationResult


def test_safety_classification_enum():
    """Test SafetyClassification enum values."""
    assert SafetyClassification.INFORMATIONAL.value == "informational"
    assert SafetyClassification.SAFE_REVERSIBLE.value == "safe_reversible"
    assert SafetyClassification.APPROVAL_REQUIRED.value == "approval_required"
    assert SafetyClassification.DESTRUCTIVE.value == "destructive"


def test_operation_context_creation():
    """Test OperationContext creation."""
    context = OperationContext(
        operation_type="index-create",
        target_resource="test-index",
        resource_type="index",
        parameters={"shards": 3, "replicas": 1},
        connection_permissions=["monitoring", "full"],
        is_write_enabled=True
    )

    assert context.operation_type == "index-create"
    assert context.target_resource == "test-index"
    assert context.resource_type == "index"
    assert context.parameters == {"shards": 3, "replicas": 1}
    assert context.connection_permissions == ["monitoring", "full"]
    assert context.is_write_enabled == True


def test_classify_operation_destructive():
    """Test classification of destructive operations."""
    destructive_ops = [
        "index-delete", "node-delete", "pvc-delete", "snapshot-delete",
        "cluster-shutdown", "data-purge", "forced-merge-expunge"
    ]

    for op in destructive_ops:
        context = OperationContext(
            operation_type=op,
            target_resource="test-resource",
            resource_type="index",
            parameters={},
            connection_permissions=["full"],
            is_write_enabled=True
        )
        classification = classify_operation(context)
        assert classification == SafetyClassification.DESTRUCTIVE, f"Failed for {op}"


def test_classify_operation_write_requires_approval():
    """Test classification of write operations that require approval."""
    write_ops = [
        "index-create", "index-update-settings", "node-add", "node-remove",
        "shard-relocate", "snapshot-create", "snapshot-restore",
        "template-put", "component-template-put"
    ]

    for op in write_ops:
        # Without write access or full permissions -> APPROVAL_REQUIRED
        context_no_write = OperationContext(
            operation_type=op,
            target_resource="test-resource",
            resource_type="index",
            parameters={},
            connection_permissions=["monitoring"],  # Only monitoring
            is_write_enabled=False
        )
        classification = classify_operation(context_no_write)
        assert classification == SafetyClassification.APPROVAL_REQUIRED, f"Failed for {op} without write access"

        # With write access and full permissions -> SAFE_REVERSIBLE
        context_with_write = OperationContext(
            operation_type=op,
            target_resource="test-resource",
            resource_type="index",
            parameters={},
            connection_permissions=["monitoring", "full"],
            is_write_enabled=True
        )
        classification = classify_operation(context_with_write)
        assert classification == SafetyClassification.SAFE_REVERSIBLE, f"Failed for {op} with write access"


def test_classify_operation_read_only():
    """Test classification of read-only operations."""
    context = OperationContext(
        operation_type="cluster-health",
        target_resource="test-cluster",
        resource_type="cluster",
        parameters={},
        connection_permissions=["monitoring"],
        is_write_enabled=False
    )
    classification = classify_operation(context)
    assert classification == SafetyClassification.INFORMATIONAL


def test_classify_operation_default_safe_reversible():
    """Test that unknown write operations default to safe reversible."""
    context = OperationContext(
        operation_type="unknown-write-op",
        target_resource="test-resource",
        resource_type="unknown",
        parameters={},
        connection_permissions=["full"],
        is_write_enabled=True
    )
    classification = classify_operation(context)
    assert classification == SafetyClassification.SAFE_REVERSIBLE


def test_policy_engine_initialization():
    """Test PolicyEngine initialization."""
    engine = PolicyEngine()
    assert engine is not None
    assert hasattr(engine, 'never_allowed_ops')
    assert hasattr(engine, 'approval_required_ops')


def test_policy_engine_evaluate_operation_never_allowed():
    """Test that never allowed operations return DENY."""
    engine = PolicyEngine()
    never_allowed_ops = [
        "index-delete", "node-delete", "pvc-delete", "snapshot-delete",
        "cluster-shutdown", "data-purge", "forced-merge-expunge"
    ]

    for op in never_allowed_ops:
        context = OperationContext(
            operation_type=op,
            target_resource="test-resource",
            resource_type="index",
            parameters={},
            connection_permissions=["full"],
            is_write_enabled=True
        )
        decision = engine.evaluate_operation(context)
        assert decision == PolicyDecision.DENY, f"Failed for {op}"


def test_policy_engine_evaluate_operation_approval_required():
    """Test that approval required operations return REQUIRE_APPROVAL when write access is not enabled."""
    engine = PolicyEngine()
    approval_ops = [
        "index-create", "index-update-settings", "node-add", "node-remove",
        "shard-relocate", "snapshot-create", "snapshot-restore",
        "template-put", "component-template-put"
    ]

    for op in approval_ops:
        # Without write access or full permissions -> REQUIRE_APPROVAL
        context_no_write = OperationContext(
            operation_type=op,
            target_resource="test-resource",
            resource_type="index",
            parameters={},
            connection_permissions=["monitoring"],  # Only monitoring
            is_write_enabled=False
        )
        decision = engine.evaluate_operation(context_no_write)
        assert decision == PolicyDecision.REQUIRE_APPROVAL, f"Failed for {op} without write access"

        # With write access and full permissions -> ALLOW (SAFE_REVERSIBLE)
        context_with_write = OperationContext(
            operation_type=op,
            target_resource="test-resource",
            resource_type="index",
            parameters={},
            connection_permissions=["monitoring", "full"],
            is_write_enabled=True
        )
        decision = engine.evaluate_operation(context_with_write)
        assert decision == PolicyDecision.ALLOW, f"Failed for {op} with write access"


def test_policy_engine_evaluate_operation_allowed():
    """Test that allowed operations return ALLOW."""
    engine = PolicyEngine()
    allowed_ops = [
        "cluster-health", "cluster-stats", "node-stats", "index-stats",
        "search", "mget", "termvectors"
    ]

    for op in allowed_ops:
        context = OperationContext(
            operation_type=op,
            target_resource="test-resource",
            resource_type="index",
            parameters={},
            connection_permissions=["monitoring"],
            is_write_enabled=False
        )
        decision = engine.evaluate_operation(context)
        assert decision == PolicyDecision.ALLOW, f"Failed for {op}"


def test_policy_engine_validate_operation_returns_violations():
    """Test that validate_operation returns appropriate violations."""
    engine = PolicyEngine()

    # Test DENY violation (never allowed ops)
    context_deny = OperationContext(
        operation_type="index-delete",
        target_resource="test-index",
        resource_type="index",
        parameters={},
        connection_permissions=["full"],
        is_write_enabled=True
    )
    violations = engine.validate_operation(context_deny)
    assert len(violations) >= 1  # May have multiple violations (denied + never allowed + not allowlisted)
    # Check that at least one is operation_denied
    assert any(v.violation_type == "operation_denied" for v in violations)
    assert any("index-delete" in v.message for v in violations)
    assert any(v.required_action == "Contact administrator for manual intervention" for v in violations)

    # Test REQUIRE_APPROVAL violation (when write access is NOT enabled)
    context_approve = OperationContext(
        operation_type="index-create",
        target_resource="test-index",
        resource_type="index",
        parameters={},
        connection_permissions=["monitoring"],  # Only monitoring, no full
        is_write_enabled=False
    )
    violations = engine.validate_operation(context_approve)
    assert len(violations) >= 1  # May have multiple violations
    # Check that at least one is approval_required
    assert any(v.violation_type == "approval_required" for v in violations)
    assert any("index-create" in v.message for v in violations)
    assert any(v.required_action == "Obtain approval through the approval workflow" for v in violations)

    # Test that with write access and full permissions, index-create is ALLOWED (no violations)
    context_with_write = OperationContext(
        operation_type="index-create",
        target_resource="test-index",
        resource_type="index",
        parameters={},
        connection_permissions=["monitoring", "full"],
        is_write_enabled=True
    )
    violations = engine.validate_operation(context_with_write)
    assert len(violations) == 0  # Should be allowed with write access

    # Test insufficient permissions violation
    context_no_write = OperationContext(
        operation_type="index-create",
        target_resource="test-index",
        resource_type="index",
        parameters={},
        connection_permissions=["monitoring"],
        is_write_enabled=False
    )
    violations = engine.validate_operation(context_no_write)
    assert len(violations) >= 1
    # Check that at least one is insufficient_permissions
    assert any(v.violation_type == "insufficient_permissions" for v in violations)
    assert any("Write access is not enabled" in v.message for v in violations)

    # Test allowed operation returns no violations
    context_allow = OperationContext(
        operation_type="cluster-health",
        target_resource="test-cluster",
        resource_type="cluster",
        parameters={},
        connection_permissions=["monitoring"],
        is_write_enabled=False
    )
    violations = engine.validate_operation(context_allow)
    assert len(violations) == 0


def test_policy_engine_is_operation_allowed():
    """Test is_operation_allowed helper method."""
    engine = PolicyEngine()

    # Should be False for never allowed
    context_deny = OperationContext(
        operation_type="index-delete",
        target_resource="test-index",
        resource_type="index",
        parameters={},
        connection_permissions=["full"],
        is_write_enabled=True
    )
    assert engine.is_operation_allowed(context_deny) == False

    # Should be False for approval required (when write access NOT enabled)
    context_approve = OperationContext(
        operation_type="index-create",
        target_resource="test-index",
        resource_type="index",
        parameters={},
        connection_permissions=["monitoring"],  # Only monitoring
        is_write_enabled=False
    )
    assert engine.is_operation_allowed(context_approve) == False

    # Should be True for index-create with write access enabled
    context_with_write = OperationContext(
        operation_type="index-create",
        target_resource="test-index",
        resource_type="index",
        parameters={},
        connection_permissions=["monitoring", "full"],
        is_write_enabled=True
    )
    assert engine.is_operation_allowed(context_with_write) == True

    # Should be True for allowed
    context_allow = OperationContext(
        operation_type="cluster-health",
        target_resource="test-cluster",
        resource_type="cluster",
        parameters={},
        connection_permissions=["monitoring"],
        is_write_enabled=False
    )
    assert engine.is_operation_allowed(context_allow) == True


def test_mutation_filter_initialization():
    """Test MutationFilter initialization."""
    filter = MutationFilter()
    assert filter is not None
    assert hasattr(filter, 'allowlisted_operations')
    assert hasattr(filter, 'never_allowed_operations')
    assert hasattr(filter, 'dry_run_required_operations')
    assert hasattr(filter, 'policy_engine')


def test_mutation_request_creation():
    """Test MutationRequest creation."""
    context = OperationContext(
        operation_type="index-delete",
        target_resource="test-index",
        resource_type="index",
        parameters={},
        connection_permissions=["full"],
        is_write_enabled=True
    )
    request = MutationRequest(
        operation_type="index-delete",
        target_resource="test-index",
        resource_type="index",
        parameters={"timeout": "30s"},
        connection_context=context
    )

    assert request.operation_type == "index-delete"
    assert request.target_resource == "test-index"
    assert request.resource_type == "index"
    assert request.parameters == {"timeout": "30s"}
    assert request.connection_context == context


def test_mutation_result_creation():
    """Test MutationResult creation."""
    violation = OperationViolation(
        violation_type="operation_denied",
        message="Operation 'index-delete' is not allowed",
        required_action="Contact administrator for manual intervention",
        context=OperationContext(
            operation_type="index-delete",
            target_resource="test-index",
            resource_type="index",
            parameters={},
            connection_permissions=["full"],
            is_write_enabled=True
        )
    )
    result = MutationResult(
        decision=MutationDecision.DENY,
        violations=[violation],
        allowed=False,
        requires_dry_run=False
    )

    assert result.decision == MutationDecision.DENY
    assert len(result.violations) == 1
    assert result.allowed == False
    assert result.requires_dry_run == False


def test_mutation_filter_filter_mutation_never_allowed():
    """Test that never allowed operations are denied."""
    filter = MutationFilter()
    never_allowed_ops = [
        "cluster-shutdown", "data-purge", "forced-merge-expunge",
        "delete-all-indices", "delete-cluster-metadata"
    ]

    for op in never_allowed_ops:
        context = OperationContext(
            operation_type=op,
            target_resource="test-resource",
            resource_type="cluster",
            parameters={},
            connection_permissions=["full"],
            is_write_enabled=True
        )
        request = MutationRequest(
            operation_type=op,
            target_resource="test-resource",
            resource_type="cluster",
            parameters={},
            connection_context=context
        )
        result = filter.filter_mutation(request)
        assert result.decision == MutationDecision.DENY
        assert result.allowed == False
        assert result.requires_dry_run == False
        assert len(result.violations) >= 1  # May have multiple violations
        # Check that at least one is operation_never_allowed
        assert any(v.violation_type == "operation_never_allowed" for v in result.violations)
        assert any("never allowed" in v.message for v in result.violations)


def test_mutation_filter_filter_mutation_not_allowlisted():
    """Test that non-allowlisted operations are denied."""
    filter = MutationFilter()
    context = OperationContext(
        operation_type="unknown-op",
        target_resource="test-resource",
        resource_type="unknown",
        parameters={},
        connection_permissions=["full"],
        is_write_enabled=True
    )
    request = MutationRequest(
        operation_type="unknown-op",
        target_resource="test-resource",
        resource_type="unknown",
        parameters={},
        connection_context=context
    )
    result = filter.filter_mutation(request)
    assert result.decision == MutationDecision.DENY
    assert result.allowed == False
    assert result.requires_dry_run == False
    assert len(result.violations) == 1
    assert "not in the allow-list" in result.violations[0].message


def test_mutation_filter_filter_mutation_requires_dry_run():
    """Test that certain operations require dry-run."""
    filter = MutationFilter()
    # Get the set of operations that require dry-run
    dry_run_required = filter.dry_run_required_operations
    # Exclude operations that are in approval_required_ops or never_allowed_ops (they are handled by other checks first)
    approval_required = filter.policy_engine.approval_required_ops
    never_allowed = filter.policy_engine.never_allowed_ops
    # Operations that require dry-run and are not otherwise blocked by approval or never allowed
    test_ops = dry_run_required - approval_required - never_allowed

    for op in test_ops:
        context = OperationContext(
            operation_type=op,
            target_resource="test-resource",
            resource_type="index",
            parameters={},
            connection_permissions=["full"],
            is_write_enabled=True
        )
        request = MutationRequest(
            operation_type=op,
            target_resource="test-resource",
            resource_type="index",
            parameters={},
            connection_context=context
        )
        result = filter.filter_mutation(request)
        # Should require dry-run when no other violations (not never allowed, not approval required)
        assert result.decision == MutationDecision.REQUIRE_DRY_RUN
        assert result.allowed == False
        assert result.requires_dry_run == True
        # Should have no violations (dry-run required but otherwise valid)
        assert len(result.violations) == 0


def test_mutation_filter_filter_mutation_allowed():
    """Test that allowlisted operations with no other issues are allowed."""
    filter = MutationFilter()
    # Operations that are allowlisted, not dry-run required, not approval required, not never allowed
    allowed_ops = filter.allowlisted_operations - filter.dry_run_required_operations - filter.policy_engine.approval_required_ops - filter.policy_engine.never_allowed_ops

    for op in allowed_ops:
        context = OperationContext(
            operation_type=op,
            target_resource="test-resource",
            resource_type="index",
            parameters={},
            connection_permissions=["full"],
            is_write_enabled=True
        )
        request = MutationRequest(
            operation_type=op,
            target_resource="test-resource",
            resource_type="index",
            parameters={},
            connection_context=context
        )
        result = filter.filter_mutation(request)
        assert result.decision == MutationDecision.ALLOW
        assert result.allowed == True
        assert result.requires_dry_run == False
        assert len(result.violations) == 0


def test_dry_run_engine_initialization():
    """Test DryRunEngine initialization."""
    engine = DryRunEngine()
    assert engine is not None


def test_diff_result_creation():
    """Test DiffResult creation."""
    diff_result = DiffResult(
        operation_type="index-delete",
        target_resource="test-index",
        before_snapshot={"timestamp": "2023-01-01T00:00:00Z", "index_count": 5},
        after_snapshot={"timestamp": "2023-01-01T00:00:01Z", "index_count": 4},
        changes_summary={"index_count": -1},
        risk_assessment="LOW - Minimal impact expected"
    )

    assert diff_result.operation_type == "index-delete"
    assert diff_result.target_resource == "test-index"
    assert diff_result.before_snapshot["index_count"] == 5
    assert diff_result.after_snapshot["index_count"] == 4
    assert diff_result.changes_summary["index_count"] == -1
    assert diff_result.risk_assessment == "LOW - Minimal impact expected"
    assert len(diff_result.diff_id) == 16  # SHA-256 truncated to 16 chars


def test_audit_store_initialization():
    """Test AuditStore initialization."""
    # Test with default path
    store = AuditStore()
    assert store is not None
    assert store.storage_path is not None
    assert store.signing_key is not None

    # Test with custom path
    custom_store = AuditStore(storage_path="/tmp/test_audit", signing_key="test-key")
    assert custom_store.storage_path == Path("/tmp/test_audit")
    assert custom_store.signing_key == "test-key"


def test_audit_entry_creation_and_serialization():
    """Test AuditEntry creation and serialization."""
    # Use a fixed timestamp to avoid serialization issues
    fixed_time = datetime(2026, 8, 20, 12, 0, 0, tzinfo=timezone.utc)
    entry = AuditEntry(
        uuid="test-uuid-123",
        timestamp=fixed_time,
        operation="index-delete",
        classification="approval_required",
        before_hash="abc123",
        after_hash="def456",
        performed_by="test-user",
        details={"index": "test-index", "shards": 3},
        signature="test-signature"
    )

    assert entry.uuid == "test-uuid-123"
    assert entry.operation == "index-delete"
    assert entry.classification == "approval_required"
    assert entry.before_hash == "abc123"
    assert entry.after_hash == "def456"
    assert entry.performed_by == "test-user"
    assert entry.details["index"] == "test-index"
    assert entry.signature == "test-signature"

    # Test to_dict serialization
    entry_dict = entry.to_dict()
    assert entry_dict["uuid"] == "test-uuid-123"
    assert entry_dict["operation"] == "index-delete"
    assert entry_dict["classification"] == "approval_required"
    assert entry_dict["before_hash"] == "abc123"
    assert entry_dict["after_hash"] == "def456"
    assert entry_dict["performed_by"] == "test-user"
    assert entry_dict["details"]["index"] == "test-index"
    assert entry_dict["signature"] == "test-signature"

    # Test from_dict deserialization
    restored_entry = AuditEntry.from_dict(entry_dict)
    assert restored_entry.uuid == entry.uuid
    assert restored_entry.operation == entry.operation
    assert restored_entry.classification == entry.classification
    assert restored_entry.before_hash == entry.before_hash
    assert restored_entry.after_hash == entry.after_hash
    assert restored_entry.performed_by == entry.performed_by
    assert restored_entry.details == entry.details
    assert restored_entry.signature == entry.signature


def test_audit_store_log_mutation():
    """Test logging a mutation to the audit store."""
    store = AuditStore(storage_path="/tmp/test_audit")

    before_state = {"index_count": 5, "cluster_health": "green"}
    after_state = {"index_count": 4, "cluster_health": "yellow"}

    entry = store.log_mutation(
        operation="index-delete",
        classification="approval_required",
        before_state=before_state,
        after_state=after_state,
        performed_by="test-user",
        details={"index": "test-index", "reason": "old_data"}
    )

    assert isinstance(entry, AuditEntry)
    assert entry.operation == "index-delete"
    assert entry.classification == "approval_required"
    assert entry.performed_by == "test-user"
    assert entry.details["index"] == "test-index"
    assert entry.details["reason"] == "old_data"
    assert len(entry.signature) > 0  # Should have a signature

    # Test that entry was stored
    assert store.get_entry_count() == 1

    # Test retrieving the entry
    retrieved_entry = store.get_entry(entry.uuid)
    assert retrieved_entry is not None
    assert retrieved_entry.uuid == entry.uuid
    assert retrieved_entry.operation == entry.operation

    # Test verifying integrity
    assert store.verify_entry_integrity(entry.uuid) == True

    # Clean up
    import shutil
    shutil.rmtree("/tmp/test_audit", ignore_errors=True)


def test_audit_store_get_entries():
    """Test retrieving entries from the audit store."""
    store = AuditStore(storage_path="/tmp/test_audit2")

    # Log multiple entries
    store.log_mutation(
        operation="index-create",
        classification="safe_reversible",
        before_state={"index_count": 3},
        after_state={"index_count": 4},
        performed_by="user1",
        details={"index": "new-index"}
    )

    store.log_mutation(
        operation="index-delete",
        classification="approval_required",
        before_state={"index_count": 4},
        after_state={"index_count": 3},
        performed_by="user2",
        details={"index": "old-index"}
    )

    # Test getting all entries
    entries = store.get_entries()
    assert len(entries) == 2
    # Should be in reverse chronological order (most recent first)
    assert entries[0].operation == "index-delete"
    assert entries[1].operation == "index-create"

    # Test filtering by operation
    create_entries = store.get_entries(operation="index-create")
    assert len(create_entries) == 1
    assert create_entries[0].operation == "index-create"

    delete_entries = store.get_entries(operation="index-delete")
    assert len(delete_entries) == 1
    assert delete_entries[0].operation == "index-delete"

    # Test filtering by user
    user1_entries = store.get_entries(performed_by="user1")
    assert len(user1_entries) == 1
    assert user1_entries[0].performed_by == "user1"

    user2_entries = store.get_entries(performed_by="user2")
    assert len(user2_entries) == 1
    assert user2_entries[0].performed_by == "user2"

    # Test limit parameter
    limited_entries = store.get_entries(limit=1)
    assert len(limited_entries) == 1

    # Clean up
    import shutil
    shutil.rmtree("/tmp/test_audit2", ignore_errors=True)


def test_audit_store_verify_all_integrity():
    """Test verifying integrity of all audit entries."""
    store = AuditStore(storage_path="/tmp/test_audit3")

    # Log some entries
    store.log_mutation(
        operation="index-create",
        classification="safe_reversible",
        before_state={"index_count": 3},
        after_state={"index_count": 4},
        performed_by="test-user",
        details={}
    )

    store.log_mutation(
        operation="index-delete",
        classification="approval_required",
        before_state={"index_count": 4},
        after_state={"index_count": 3},
        performed_by="test-user",
        details={}
    )

    # All entries should verify
    assert store.verify_all_integrity() == True

    # Clean up
    import shutil
    shutil.rmtree("/tmp/test_audit3", ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])