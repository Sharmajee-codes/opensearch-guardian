"""
Unit tests for the Security & Safety Engine audit store.
Tests immutable audit logging and signature verification.
"""

import pytest
import tempfile
import os
from pathlib import Path
from guardian.safety.audit_store import AuditStore, AuditEntry


class TestAuditStore:
    """Tests for AuditStore."""

    @pytest.fixture
    def audit_store(self, tmp_path):
        """Create an AuditStore with temporary storage."""
        store_path = tmp_path / "audit"
        return AuditStore(storage_path=str(store_path))

    def test_log_mutation_creates_entry(self, audit_store):
        """Test that logging a mutation creates an audit entry."""
        before_state = {"nodes": [{"id": "node-1"}]}
        after_state = {
            "nodes": [{"id": "node-1"}, {"id": "node-2"}],
            "cluster_stats": {"total_nodes": 2}
        }

        entry = audit_store.log_mutation(
            operation="node-add",
            classification="safe_reversible",
            before_state=before_state,
            after_state=after_state,
            performed_by="test-user",
            details={"role": "data"}
        )

        assert isinstance(entry, AuditEntry)
        assert entry.operation == "node-add"
        assert entry.classification == "safe_reversible"
        assert entry.performed_by == "test-user"
        assert len(entry.before_hash) > 0
        assert len(entry.after_hash) > 0
        assert len(entry.signature) > 0
        assert entry.details == {"role": "data"}

    def test_entry_integrity_verification(self, audit_store):
        """Test that audit entry signatures can be verified."""
        before_state = {"data": "test"}
        after_state = {"data": "updated"}

        entry = audit_store.log_mutation(
            operation="test",
            classification="informational",
            before_state=before_state,
            after_state=after_state,
            performed_by="user",
            details={}
        )

        # Verify the entry
        assert audit_store.verify_entry_integrity(entry.uuid) is True
        assert audit_store.verify_all_integrity() is True

    def test_tampered_entry_fails_verification(self, audit_store):
        """Test that tampered entries fail verification."""
        before_state = {"data": "original"}
        after_state = {"data": "touched"}

        entry = audit_store.log_mutation(
            operation="test",
            classification="informational",
            before_state=before_state,
            after_state=after_state,
            performed_by="user",
            details={}
        )

        # Tamper with the entry
        entry.before_hash = "0" * 64
        entry.signature = "tampered-signature"

        # Verification should fail
        assert audit_store.verify_entry_integrity(entry.uuid) is False

    def test_get_entries_filters_by_operation(self, audit_store):
        """Test filtering entries by operation type."""
        # Log multiple entries
        audit_store.log_mutation(
            operation="node-add",
            classification="safe_reversible",
            before_state={},
            after_state={},
            performed_by="user1",
            details={}
        )
        audit_store.log_mutation(
            operation="index-create",
            classification="safe_reversible",
            before_state={},
            after_state={},
            performed_by="user1",
            details={}
        )
        audit_store.log_mutation(
            operation="node-add",
            classification="safe_reversible",
            before_state={},
            after_state={},
            performed_by="user2",
            details={}
        )

        # Filter by operation
        node_add_entries = audit_store.get_entries(operation="node-add")
        assert len(node_add_entries) == 2

        index_entries = audit_store.get_entries(operation="index-create")
        assert len(index_entries) == 1

    def test_get_entries_filters_by_performer(self, audit_store):
        """Test filtering entries by performer."""
        # Log entries for different users
        audit_store.log_mutation(
            operation="test",
            classification="informational",
            before_state={},
            after_state={},
            performed_by="user1",
            details={}
        )
        audit_store.log_mutation(
            operation="test",
            classification="informational",
            before_state={},
            after_state={},
            performed_by="user2",
            details={}
        )

        # Filter by performer
        user1_entries = audit_store.get_entries(performed_by="user1")
        assert len(user1_entries) == 1
        assert user1_entries[0].performed_by == "user1"

    def test_get_entry_by_uuid(self, audit_store):
        """Test retrieving a specific entry by UUID."""
        before_state = {"data": "before"}
        after_state = {"data": "after"}

        entry = audit_store.log_mutation(
            operation="test",
            classification="informational",
            before_state=before_state,
            after_state=after_state,
            performed_by="user",
            details={}
        )

        # Retrieve by UUID
        retrieved = audit_store.get_entry(entry.uuid)
        assert retrieved is not None
        assert retrieved.uuid == entry.uuid
        assert retrieved.operation == "test"

    def test_get_entry_not_found(self, audit_store):
        """Test retrieving a non-existent entry."""
        entry = audit_store.get_entry("non-existent-uuid")
        assert entry is None

    def test_get_entry_count(self, audit_store):
        """Test counting audit entries."""
        assert audit_store.get_entry_count() == 0

        # Log entries
        audit_store.log_mutation(
            operation="test1",
            classification="informational",
            before_state={},
            after_state={},
            performed_by="user",
            details={}
        )
        audit_store.log_mutation(
            operation="test2",
            classification="safe_reversible",
            before_state={},
            after_state={},
            performed_by="user",
            details={}
        )

        assert audit_store.get_entry_count() == 2

    def test_get_last_n_entries(self, audit_store):
        """Test retrieving the last N entries."""
        # Log multiple entries
        for i in range(5):
            audit_store.log_mutation(
                operation="test",
                classification="informational",
                before_state={},
                after_state={},
                performed_by="user",
                details={}
            )

        last_2 = audit_store.get_last_n_entries(2)
        assert len(last_2) == 2

        last_5 = audit_store.get_last_n_entries(5)
        assert len(last_5) == 5

    def test_persistence_across_instances(self, tmp_path):
        """Test that entries persist across AuditStore instances."""
        store_path = tmp_path / "persistent-audit"

        # Create first instance and log entries
        store1 = AuditStore(storage_path=str(store_path))
        store1.log_mutation(
            operation="node-add",
            classification="safe_reversible",
            before_state={"nodes": 2},
            after_state={"nodes": 3},
            performed_by="admin",
            details={}
        )

        # Create second instance from same path
        store2 = AuditStore(storage_path=str(store_path))
        entries = store2.get_entries()
        assert len(entries) == 1
        assert entries[0].operation == "node-add"

    def test_entry_serialization(self, audit_store):
        """Test that audit entries can be serialized to/from dicts."""
        before_state = {"data": "test"}
        after_state = {"data": "updated"}

        entry = audit_store.log_mutation(
            operation="test",
            classification="informational",
            before_state=before_state,
            after_state=after_state,
            performed_by="user",
            details={"key": "value"}
        )

        # Serialize
        data = entry.to_dict()
        assert "uuid" in data
        assert "timestamp" in data
        assert "operation" in data
        assert "signature" in data

        # Deserialize
        restored = AuditEntry.from_dict(data)
        assert restored.uuid == entry.uuid
        assert restored.operation == entry.operation
        assert restored.signature == entry.signature

    def test_multiple_entries_have_unique_uuids(self, audit_store):
        """Test that each entry has a unique UUID."""
        entry1 = audit_store.log_mutation(
            operation="test1",
            classification="informational",
            before_state={},
            after_state={},
            performed_by="user",
            details={}
        )
        entry2 = audit_store.log_mutation(
            operation="test2",
            classification="informational",
            before_state={},
            after_state={},
            performed_by="user",
            details={}
        )

        assert entry1.uuid != entry2.uuid

    def test_timestamp_ordering(self, audit_store):
        """Test that timestamps are ordered chronologically."""
        import time

        entry1 = audit_store.log_mutation(
            operation="test1",
            classification="informational",
            before_state={},
            after_state={},
            performed_by="user",
            details={}
        )

        time.sleep(0.01)  # Small delay

        entry2 = audit_store.log_mutation(
            operation="test2",
            classification="informational",
            before_state={},
            after_state={},
            performed_by="user",
            details={}
        )

        assert entry2.timestamp > entry1.timestamp
