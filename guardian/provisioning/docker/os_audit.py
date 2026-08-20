"""OpenSearch-backed Audit Trail for Provisioning Operations.

This module provides an immutable audit trail that stores entries in an OpenSearch
index, replacing the local file-based audit store. Entries are HMAC-signed for
verification and can be correlated with OpenSearch security audit logs.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AuditEntry:
    """Immutable audit log entry for provisioning operations."""

    entry_id: str
    timestamp: datetime
    operation: str
    classification: str  # "informational", "safe_reversible", "approval_required", "destructive"
    before_state_hash: str
    after_state_hash: str
    performed_by: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    signature: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for storage."""
        timestamp_str = self.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        return {
            "entry_id": self.entry_id,
            "timestamp": timestamp_str,
            "operation": self.operation,
            "classification": self.classification,
            "before_state_hash": self.before_state_hash,
            "after_state_hash": self.after_state_hash,
            "performed_by": self.performed_by,
            "details": self.details,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuditEntry:
        """Deserialize from dictionary."""
        timestamp_str = data["timestamp"]
        if timestamp_str.endswith("Z"):
            timestamp_str = timestamp_str.replace("Z", "+00:00")
        return cls(
            entry_id=data["entry_id"],
            timestamp=datetime.fromisoformat(timestamp_str),
            operation=data["operation"],
            classification=data["classification"],
            before_state_hash=data["before_state_hash"],
            after_state_hash=data["after_state_hash"],
            performed_by=data.get("performed_by"),
            details=data.get("details", {}),
            signature=data.get("signature", ""),
        )

    def verify_signature(self, signing_key: str) -> bool:
        """Verify the HMAC signature of this entry."""
        entry_data = f"{self.entry_id}{self.timestamp.isoformat()}{self.operation}{self.before_state_hash}{self.after_state_hash}{self.performed_by or ''}"
        expected = hmac.new(
            signing_key.encode(),
            entry_data.encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, self.signature)


class OpenSearchAuditStore:
    """
    Immutable audit log stored in OpenSearch index.

    Provides write-once semantics per SOP §8 and ADR-002.
    Entries are HMAC-signed for tamper detection and can be
    correlated with OpenSearch security audit logs.
    """

    INDEX_NAME = ".guardian-audit"
    MAX_RETRIES = 3
    RETRY_DELAY = 0.1  # seconds

    def __init__(self, client: Any, signing_key: str = None):
        """
        Initialize audit store.

        Args:
            client: OpenSearch client instance
            signing_key: HMAC signing key (defaults to random UUID)
        """
        self.client = client
        self.signing_key = signing_key or uuid.uuid4().hex
        self._ensure_index_exists()

    def _ensure_index_exists(self):
        """Create audit index if it doesn't exist with proper mappings."""
        if not self.client.indices.exists(index=self.INDEX_NAME):
            self.client.indices.create(
                index=self.INDEX_NAME,
                body={
                    "mappings": {
                        "properties": {
                            "entry_id": {"type": "keyword"},
                            "timestamp": {"type": "date"},
                            "operation": {"type": "keyword"},
                            "classification": {"type": "keyword"},
                            "before_state_hash": {"type": "keyword"},
                            "after_state_hash": {"type": "keyword"},
                            "performed_by": {"type": "keyword"},
                            "details": {"type": "object", "dynamic": True},
                            "signature": {"type": "keyword"},
                        }
                    },
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 1,
                        "refresh_interval": "-1",  # Disable auto-refresh for write performance
                    },
                },
            )
            logger.info("Created audit index: %s", self.INDEX_NAME)
        else:
            logger.debug("Audit index %s already exists", self.INDEX_NAME)

    def log_mutation(
        self,
        operation: str,
        classification: str,
        before_state: Any,
        after_state: Any,
        performed_by: str,
        details: dict[str, Any] | None = None,
    ) -> AuditEntry:
        """
        Log a mutation operation to the audit trail.

        Args:
            operation: Operation type (e.g., "node-add", "config-change")
            classification: Safety classification
            before_state: State before operation
            after_state: State after operation
            performed_by: User or system that performed the operation
            details: Additional operation details

        Returns:
            AuditEntry with signature for verification
        """
        entry_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC)

        before_hash = self._compute_hash(before_state)
        after_hash = self._compute_hash(after_state)

        entry = AuditEntry(
            entry_id=entry_id,
            timestamp=timestamp,
            operation=operation,
            classification=classification,
            before_state_hash=before_hash,
            after_state_hash=after_hash,
            performed_by=performed_by,
            details=details or {},
            signature=self._sign_entry(entry_id, timestamp, operation, before_hash, after_hash, performed_by),
        )

        # Store in OpenSearch
        self._store_entry(entry)

        logger.info(
            "Audit entry created: op=%s classification=%s performed_by=%s",
            operation,
            classification,
            performed_by,
        )

        return entry

    def log_preflight_check(
        self,
        operation_id: str,
        check_name: str,
        check_type: str,
        status: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> AuditEntry:
        """Log a preflight check result."""
        entry = AuditEntry(
            entry_id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC),
            operation=f"preflight:{operation_id}",
            classification="informational",
            before_state_hash="",
            after_state_hash="",
            performed_by="system",
            details={
                "operation_id": operation_id,
                "check_name": check_name,
                "check_type": check_type,
                "status": status,
                "message": message,
                **(details or {}),
            },
            signature=self._sign_entry(
                entry.entry_id,
                entry.timestamp,
                entry.operation,
                entry.before_state_hash,
                entry.after_state_hash,
                entry.performed_by,
            ),
        )
        self._store_entry(entry)
        return entry

    def log_provisioning_operation(
        self,
        operation_id: str,
        operation_type: str,
        details: dict[str, Any],
    ) -> AuditEntry:
        """Log a provisioning operation start/completion."""
        entry = AuditEntry(
            entry_id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC),
            operation=operation_type,
            classification="informational",
            before_state_hash="",
            after_state_hash="",
            performed_by=details.get("performed_by", "system"),
            details={
                "operation_id": operation_id,
                "timestamp": datetime.now(UTC).isoformat(),
                **details,
            },
            signature=self._sign_entry(
                entry.entry_id,
                entry.timestamp,
                entry.operation,
                entry.before_state_hash,
                entry.after_state_hash,
                entry.performed_by,
            ),
        )
        self._store_entry(entry)
        return entry

    def get_entries(
        self,
        operation: str | None = None,
        performed_by: str | None = None,
        since: str | None = None,
        limit: int = 100,
    ) -> list[AuditEntry]:
        """
        Retrieve audit entries with optional filtering.

        Args:
            operation: Filter by operation type
            performed_by: Filter by user
            since: ISO timestamp to filter entries after this time
            limit: Maximum number of entries to return

        Returns:
            List of AuditEntry objects
        """
        query: dict[str, Any] = {"query": {"bool": {"must": []}}}

        if operation:
            query["query"]["bool"]["must"].append({"term": {"operation": operation}})
        if performed_by:
            query["query"]["bool"]["must"].append({"term": {"performed_by": performed_by}})
        if since:
            query["query"]["bool"]["filter"] = [{"range": {"timestamp": {"gte": since}}}]

        query["size"] = limit
        query["sort"] = [{"timestamp": {"order": "desc"}}]

        try:
            response = self.client.search(index=self.INDEX_NAME, body=query)
            entries = []
            for hit in response["hits"]["hits"]:
                entry_data = hit["_source"]
                entry_data["timestamp"] = entry_data.get("timestamp", "")
                entries.append(AuditEntry.from_dict(entry_data))
            return entries
        except Exception as e:
            logger.error("Failed to retrieve audit entries: %s", e)
            return []

    def get_entry(self, entry_id: str) -> AuditEntry | None:
        """Retrieve a specific audit entry by ID."""
        try:
            response = self.client.get(index=self.INDEX_NAME, id=entry_id)
            if response["found"]:
                entry_data = response["_source"]
                entry_data["timestamp"] = entry_data.get("timestamp", "")
                return AuditEntry.from_dict(entry_data)
        except Exception as e:
            logger.error("Failed to retrieve audit entry %s: %s", entry_id, e)
        return None

    def verify_entry_integrity(self, entry: AuditEntry) -> bool:
        """Verify the integrity of an audit entry."""
        return entry.verify_signature(self.signing_key)

    def verify_all_integrity(self) -> bool:
        """Verify the integrity of all audit entries (sample-based for large indices)."""
        try:
            # Sample up to 100 entries for verification
            response = self.client.search(
                index=self.INDEX_NAME,
                body={"query": {"match_all": {}}, "size": 100},
            )
            for hit in response["hits"]["hits"]:
                entry_data = hit["_source"]
                entry_data["timestamp"] = entry_data.get("timestamp", "")
                entry = AuditEntry.from_dict(entry_data)
                if not entry.verify_signature(self.signing_key):
                    logger.error("Audit entry integrity check failed: %s", entry.entry_id)
                    return False
            return True
        except Exception as e:
            logger.error("Failed to verify audit integrity: %s", e)
            return False

    def get_entry_count(self) -> int:
        """Get total number of audit entries."""
        try:
            response = self.client.count(index=self.INDEX_NAME)
            return response["count"]
        except Exception:
            return 0

    def _compute_hash(self, state: Any) -> str:
        """Compute SHA-256 hash of state."""
        state_json = json.dumps(state, sort_keys=True, default=str)
        return hashlib.sha256(state_json.encode()).hexdigest()

    def _sign_entry(
        self,
        entry_id: str,
        timestamp: datetime,
        operation: str,
        before_hash: str,
        after_hash: str,
        performed_by: str | None,
    ) -> str:
        """Sign an audit entry with HMAC-SHA256."""
        entry_data = f"{entry_id}{timestamp.isoformat()}{operation}{before_hash}{after_hash}{performed_by or ''}"
        return hmac.new(
            self.signing_key.encode(),
            entry_data.encode(),
            hashlib.sha256,
        ).hexdigest()

    def _store_entry(self, entry: AuditEntry):
        """Store an audit entry in OpenSearch."""
        doc = entry.to_dict()
        doc_id = entry.entry_id

        # Retry logic for transient failures
        for attempt in range(self.MAX_RETRIES):
            try:
                self.client.index(
                    index=self.INDEX_NAME,
                    id=doc_id,
                    body=doc,
                    refresh="wait_for",  # Ensure entry is searchable
                )
                return
            except Exception as e:
                logger.warning("Failed to store audit entry (attempt %d): %s", attempt + 1, e)
                if attempt < self.MAX_RETRIES - 1:
                    import time
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                else:
                    raise

    def correlate_with_security_audit(self, entry: AuditEntry) -> dict[str, Any]:
        """
        Correlate a Guardian audit entry with OpenSearch security audit logs.

        This helps trace the full security context of an operation.
        """
        correlation = {
            "guardian_entry": entry.entry_id,
            "security_audit_queries": [],
        }

        # Query security audit for related events
        timestamp = entry.timestamp.isoformat()
        try:
            # Look for authentication events around the same time
            auth_query = {
                "query": {
                    "bool": {
                        "filter": [
                            {"range": {"timestamp": {"gte": timestamp, "lte": f"{timestamp.split('.')[0]}+00:01"}}},
                            {"term": {"action": "auth"}},
                        ]
                    }
                },
                "size": 10,
            }
            response = self.client.search(index="security-audit", body=auth_query)
            correlation["security_audit_queries"].append({
                "query": "authentication",
                "count": response["hits"]["total"]["value"],
                "samples": [hit["_source"] for hit in response["hits"]["hits"][:3]],
            })
        except Exception as e:
            logger.warning("Failed to correlate with security audit: %s", e)

        return correlation