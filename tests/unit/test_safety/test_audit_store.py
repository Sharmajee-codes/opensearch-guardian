"""Unit tests for AuditStore."""

import pytest
from pathlib import Path
from guardian.safety.audit_store import AuditStore, AuditEntry


class TestAuditEntry:
    """Tests for AuditEntry model."""

    def test_to_dict_roundtrip(self):
        entry = AuditEntry(
            uuid="test-uuid-123",
            timestamp=__import__("datetime").datetime(2026, 8, 19, 10, 0, 0),
            operation="index-create",
            classification="safe_reversible",
            before_hash="abc123",
            after_hash="def456",
            performed_by="admin",
            details={"index": "test"},
            signature="sig123",
        )
        data = entry.to_dict()
        assert data["uuid"] == "test-uuid-123"
        assert data["operation"] == "index-create"
        assert data["classification"] == "safe_reversible"
        assert data["signature"] == "sig123"

    def test_from_dict_roundtrip(self):
        from datetime import datetime
        data = {
            "uuid": "test-uuid",
            "timestamp": "2026-08-19T10:00:00+00:00",
            "operation": "snapshot-create",
            "classification": "safe_reversible",
            "before_hash": "hash1",
            "after_hash": "hash2",
            "performed_by": "user1",
            "details": {},
            "signature": "sig",
        }
        entry = AuditEntry.from_dict(data)
        assert entry.uuid == "test-uuid"
        assert entry.operation == "snapshot-create"
        assert isinstance(entry.timestamp, datetime)


class TestAuditStore:
    """Tests for AuditStore."""

    def test_default_storage_path(self, tmp_audit_path):
        store = AuditStore(storage_path=tmp_audit_path)
        assert store.storage_path == tmp_audit_path

    def test_signing_key_generated(self, tmp_audit_path):
        store = AuditStore(storage_path=tmp_audit_path)
        assert len(store.signing_key) > 0

    def test_custom_signing_key(self, tmp_audit_path):
        store = AuditStore(storage_path=tmp_audit_path, signing_key="test-key")
        assert store.signing_key == "test-key"

    def test_log_mutation_returns_entry(self, tmp_audit_path):
        store = AuditStore(storage_path=tmp_audit_path)
        entry = store.log_mutation(
            operation="index-create",
            classification="safe_reversible",
            before_state={"indices": []},
            after_state={"indices": ["test"]},
            performed_by="admin",
            details={},
        )
        assert isinstance(entry, AuditEntry)
        assert entry.operation == "index-create"
        assert entry.signature != ""

    def test_log_mutation_increments_count(self, tmp_audit_path):
        store = AuditStore(storage_path=tmp_audit_path)
        store.log_mutation(
            operation="op1",
            classification="info",
            before_state={},
            after_state={},
            performed_by="u",
            details={},
        )
        store.log_mutation(
            operation="op2",
            classification="info",
            before_state={},
            after_state={},
            performed_by="u",
            details={},
        )
        assert store.get_entry_count() == 2

    def test_get_entries_returns_all(self, tmp_audit_path):
        store = AuditStore(storage_path=tmp_audit_path)
        store.log_mutation("op1", "info", {}, {}, "u", {})
        store.log_mutation("op2", "info", {}, {}, "u", {})
        entries = store.get_entries()
        assert len(entries) == 2

    def test_get_entries_filters_by_operation(self, tmp_audit_path):
        store = AuditStore(storage_path=tmp_audit_path)
        store.log_mutation("op1", "info", {}, {}, "u", {})
        store.log_mutation("op2", "info", {}, {}, "u", {})
        entries = store.get_entries(operation="op1")
        assert len(entries) == 1
        assert entries[0].operation == "op1"

    def test_get_entries_filters_by_performed_by(self, tmp_audit_path):
        store = AuditStore(storage_path=tmp_audit_path)
        store.log_mutation("op1", "info", {}, {}, "admin", {})
        store.log_mutation("op2", "info", {}, {}, "user", {})
        entries = store.get_entries(performed_by="admin")
        assert len(entries) == 1
        assert entries[0].performed_by == "admin"

    def test_get_entry_by_uuid(self, tmp_audit_path):
        store = AuditStore(storage_path=tmp_audit_path)
        entry1 = store.log_mutation("op1", "info", {}, {}, "u", {})
        entry2 = store.log_mutation("op2", "info", {}, {}, "u", {})
        found = store.get_entry(entry1.uuid)
        assert found is not None
        assert found.uuid == entry1.uuid

    def test_get_entry_missing(self, tmp_audit_path):
        store = AuditStore(storage_path=tmp_audit_path)
        found = store.get_entry("nonexistent-uuid")
        assert found is None

    def test_verify_entry_integrity(self, tmp_audit_path):
        store = AuditStore(storage_path=tmp_audit_path)
        entry = store.log_mutation("op", "info", {}, {}, "u", {})
        assert store.verify_entry_integrity(entry.uuid) is True

    def test_verify_all_integrity(self, tmp_audit_path):
        store = AuditStore(storage_path=tmp_audit_path)
        store.log_mutation("op1", "info", {}, {}, "u", {})
        store.log_mutation("op2", "info", {}, {}, "u", {})
        assert store.verify_all_integrity() is True

    def test_get_last_n_entries(self, tmp_audit_path):
        store = AuditStore(storage_path=tmp_audit_path)
        store.log_mutation("op1", "info", {}, {}, "u", {})
        store.log_mutation("op2", "info", {}, {}, "u", {})
        store.log_mutation("op3", "info", {}, {}, "u", {})
        last = store.get_last_n_entries(2)
        assert len(last) == 2
        assert last[0].operation == "op3"
        assert last[1].operation == "op2"

    def test_get_last_n_more_than_available(self, tmp_audit_path):
        store = AuditStore(storage_path=tmp_audit_path)
        store.log_mutation("op1", "info", {}, {}, "u", {})
        last = store.get_last_n_entries(10)
        assert len(last) == 1

    def test_hash_is_deterministic(self, tmp_audit_path):
        store = AuditStore(storage_path=tmp_audit_path)
        h1 = store._compute_hash({"key": "value"})
        h2 = store._compute_hash({"key": "value"})
        assert h1 == h2
        assert h1 != store._compute_hash({"key": "other"})
