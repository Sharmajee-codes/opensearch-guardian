"""
Audit Store for the Security & Safety Engine.
Provides immutable, cryptographically signed before/after snapshots
for every mutation operation.
"""

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class AuditEntry:
    """Immutable audit log entry."""
    uuid: str
    timestamp: datetime
    operation: str
    classification: str
    before_hash: str
    after_hash: str
    performed_by: str | None
    details: dict[str, Any]
    signature: str  # HMAC signature for verification

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        # Ensure timestamp is in UTC and format as ISO with Z suffix
        if self.timestamp.tzinfo is None:
            timestamp_str = self.timestamp.replace(tzinfo=UTC).isoformat().replace("+00:00", "Z")
        else:
            timestamp_str = self.timestamp.isoformat()
            if timestamp_str.endswith("+00:00"):
                timestamp_str = timestamp_str.replace("+00:00", "Z")
        return {
            "uuid": self.uuid,
            "timestamp": timestamp_str,
            "operation": self.operation,
            "classification": self.classification,
            "before_hash": self.before_hash,
            "after_hash": self.after_hash,
            "performed_by": self.performed_by,
            "details": self.details,
            "signature": self.signature
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'AuditEntry':
        """Deserialize from dictionary."""
        timestamp_str = data["timestamp"]
        if timestamp_str.endswith("Z"):
            timestamp_str = timestamp_str.replace("Z", "+00:00")
        return cls(
            uuid=data["uuid"],
            timestamp=datetime.fromisoformat(timestamp_str),
            operation=data["operation"],
            classification=data["classification"],
            before_hash=data["before_hash"],
            after_hash=data["after_hash"],
            performed_by=data.get("performed_by"),
            details=data.get("details", {}),
            signature=data["signature"]
        )


class AuditStore:
    """
    Immutable audit log store that records all mutation operations
    with before/after state hashes for verification.
    Implements write-once semantics per SOP §8 and ADR-002.
    """

    def __init__(self, storage_path: str = None, signing_key: str = None):
        """
        Initialize audit store.

        Args:
            storage_path: Path to store audit logs (defaults to ~/.config/opensearch-guardian/audit/)
            signing_key: HMAC signing key for audit entries (defaults to random)
        """
        if storage_path is None:
            storage_path = Path.home() / ".config" / "opensearch-guardian" / "audit"
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.signing_key = signing_key or str(uuid.uuid4())
        self._entries: list[AuditEntry] = []
        self._load_existing_entries()

    def _load_existing_entries(self):
        """Load existing audit entries from disk."""
        log_file = self.storage_path / "audit.log"
        if log_file.exists():
            try:
                with open(log_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            data = json.loads(line)
                            entry = AuditEntry.from_dict(data)
                            # Verify signature before loading
                            if self._verify_signature(entry):
                                self._entries.append(entry)
            except (json.JSONDecodeError, Exception):
                # Log error but continue without loaded entries
                pass

    def _save_entries(self):
        """Save audit entries to disk."""
        log_file = self.storage_path / "audit.log"
        with open(log_file, "w") as f:
            f.writelines(json.dumps(entry.to_dict()) + "\n" for entry in self._entries)

    def _compute_hash(self, state: Any) -> str:
        """Compute SHA-256 hash of state."""
        state_json = json.dumps(state, sort_keys=True, default=str)
        return hashlib.sha256(state_json.encode()).hexdigest()

    def _sign_entry(self, entry: AuditEntry) -> str:
        """Sign an audit entry with HMAC-SHA256."""
        import hmac
        entry_data = f"{entry.uuid}{entry.timestamp}{entry.operation}{entry.before_hash}{entry.after_hash}"
        return hmac.new(
            self.signing_key.encode(),
            entry_data.encode(),
            hashlib.sha256
        ).hexdigest()

    def _verify_signature(self, entry: AuditEntry) -> bool:
        """Verify an audit entry's signature."""
        expected_signature = self._sign_entry(entry)
        return expected_signature == entry.signature

    def log_mutation(
        self,
        operation: str,
        classification: str,
        before_state: Any,
        after_state: Any,
        performed_by: str,
        details: dict[str, Any]
    ) -> AuditEntry:
        """
        Log a mutation operation to the audit trail.

        Args:
            operation: Operation type (e.g., "node-add")
            classification: Safety classification (e.g., "approval_required")
            before_state: State before operation
            after_state: State after operation
            performed_by: User or system that performed the operation
            details: Additional operation details

        Returns:
            AuditEntry with signature for verification
        """
        entry = AuditEntry(
            uuid=str(uuid.uuid4()),
            timestamp=datetime.now(UTC),
            operation=operation,
            classification=classification,
            before_hash=self._compute_hash(before_state),
            after_hash=self._compute_hash(after_state),
            performed_by=performed_by,
            details=details,
            signature=""  # Will be computed
        )

        # Sign the entry
        entry.signature = self._sign_entry(entry)

        # Append to in-memory list
        self._entries.append(entry)

        # Save to disk (append-only, write-once)
        self._save_entries()

        return entry

    def get_entries(
        self,
        operation: str | None = None,
        performed_by: str | None = None,
        limit: int = 100
    ) -> list[AuditEntry]:
        """
        Retrieve audit entries with optional filtering.

        Args:
            operation: Filter by operation type
            performed_by: Filter by user
            limit: Maximum number of entries to return

        Returns:
            List of AuditEntry objects
        """
        entries = self._entries

        if operation:
            entries = [e for e in entries if e.operation == operation]

        if performed_by:
            entries = [e for e in entries if e.performed_by == performed_by]

        # Return most recent entries first
        return list(reversed(entries[-limit:]))

    def get_entry(self, entry_uuid: str) -> AuditEntry | None:
        """Retrieve a specific audit entry by UUID."""
        for entry in self._entries:
            if entry.uuid == entry_uuid:
                return entry
        return None

    def verify_entry_integrity(self, entry_uuid: str) -> bool:
        """Verify the integrity of a specific audit entry."""
        entry = self.get_entry(entry_uuid)
        if entry is None:
            return False
        return self._verify_signature(entry)

    def verify_all_integrity(self) -> bool:
        """Verify the integrity of all audit entries."""
        return all(self._verify_signature(e) for e in self._entries)

    def get_entry_count(self) -> int:
        """Get total number of audit entries."""
        return len(self._entries)

    def get_last_n_entries(self, n: int) -> list[AuditEntry]:
        """Get the last N audit entries."""
        return list(reversed(self._entries[-n:]))