"""Snapshot Store — shared buffer of normalized snapshots.

Implements the in-memory + SQLite snapshot store from the connection-and-collection design.
"""
from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from guardian.collectors.tiers.enums import Tier
from guardian.core_types.connection_models import ConnectionProfile
from guardian.models import CollectionResult

logger = logging.getLogger(__name__)


@dataclass
class SnapshotEntry:
    """Entry in the snapshot history."""

    id: str
    timestamp: datetime
    tier: Tier
    snapshot: Any  # ClusterSnapshot, NodeSnapshot, etc.


class SnapshotStore:
    """Shared in-memory (plus SQLite-persisted) buffer of normalized snapshots.

    Responsibilities:
    - Store latest snapshot per tier
    - Maintain rolling history window (configurable, default 1000 entries)
    - Provide subscription mechanism for real-time updates
    - Persist history to SQLite for trend analysis
    """

    def __init__(
        self,
        connection: ConnectionProfile,
        history_window: int = 1000,
        db_path: Path | None = None,
    ) -> None:
        self.connection = connection
        self.history_window = history_window

        # In-memory storage
        self._latest: dict[Tier, Any] = {}
        self._history: deque[SnapshotEntry] = deque(maxlen=history_window)
        self._subscribers: dict[Tier, list[Callable[[Any], None]]] = {
            tier: [] for tier in Tier
        }
        self._lock = __import__("threading").RLock()
        self._msg_counter = 0

        # SQLite persistence
        if db_path is None:
            db_path = Path.home() / ".config" / "opensearch-guardian" / "snapshots.db"
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite database for snapshot persistence."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS snapshots (
                    id TEXT PRIMARY KEY,
                    connection_id TEXT NOT NULL,
                    tier TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    snapshot_json TEXT NOT NULL,
                    snapshot_hash TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_snapshots_connection_tier_time
                ON snapshots(connection_id, tier, timestamp)
                """
            )
            conn.commit()

    def _compute_hash(self, snapshot: Any) -> str:
        """Compute SHA-256 hash of snapshot for immutability verification."""
        snapshot_json = json.dumps(snapshot, sort_keys=True, default=str)
        return hashlib.sha256(snapshot_json.encode()).hexdigest()

    def push(self, result: CollectionResult, tier: Tier) -> None:
        """Push a new collection result for a tier."""
        snapshot = self._extract_snapshot(result, tier)
        if snapshot is None:
            return

        with self._lock:
            # Store latest
            self._latest[tier] = snapshot

            # Add to history
            self._msg_counter += 1
            entry = SnapshotEntry(
                id=str(uuid4()),
                timestamp=datetime.now(),
                tier=tier,
                snapshot=snapshot,
            )
            self._history.append(entry)

            # Persist to SQLite
            snapshot_json = json.dumps(snapshot, sort_keys=True, default=str)
            snapshot_hash = self._compute_hash(snapshot)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO snapshots
                    (id, connection_id, tier, timestamp, snapshot_json, snapshot_hash)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry.id,
                        self.connection.id,
                        tier.value,
                        entry.timestamp.isoformat(),
                        snapshot_json,
                        snapshot_hash,
                    ),
                )
                conn.commit()

        # Notify subscribers
        self._notify_subscribers(tier, snapshot)

    def _extract_snapshot(self, result: CollectionResult, tier: Tier) -> Any:
        """Extract the relevant snapshot from a CollectionResult."""
        if tier == Tier.T1:
            return result.cluster_snapshot
        elif tier == Tier.T2:
            return result.node_snapshots or {}
        elif tier == Tier.T3:
            return result.index_snapshots
        elif tier == Tier.T4:
            return getattr(result, "diagnostic_snapshot", None) or {}
        else:
            return None

    def get_latest(self, tier: Tier) -> Any | None:
        """Get the most recent snapshot for a tier."""
        with self._lock:
            return self._latest.get(tier)

    def get_history(
        self,
        tier: Tier,
        since: datetime | None = None,
        limit: int | None = None,
    ) -> list[SnapshotEntry]:
        """Get historical snapshots for a tier."""
        with self._lock:
            history = list(self._history)
            if since is not None:
                history = [e for e in history if e.timestamp >= since]
            history = [e for e in history if e.tier == tier]
            if limit is not None:
                history = history[-limit:]
            return list(reversed(history))  # Most recent first

    def subscribe(
        self, tier: Tier, callback: Callable[[Any], None]
    ) -> Callable[[], None]:
        """Subscribe to snapshot updates for a tier.

        Returns an unsubscribe function.
        """
        with self._lock:
            self._subscribers[tier].append(callback)

        def unsubscribe() -> None:
            with self._lock:
                if callback in self._subscribers[tier]:
                    self._subscribers[tier].remove(callback)

        return unsubscribe

    def _notify_subscribers(self, tier: Tier, snapshot: Any) -> None:
        """Notify all subscribers of a new snapshot."""
        with self._lock:
            subscribers = list(self._subscribers[tier])
        for callback in subscribers:
            try:
                callback(tier, snapshot)
            except Exception:
                logger.exception("Snapshot subscriber callback failed for tier %s", tier)

    def get_stats(self) -> dict[str, Any]:
        """Get store statistics."""
        with self._lock:
            return {
                "connection_id": self.connection.id,
                "history_size": len(self._history),
                "latest_tiers": [t.value for t, s in self._latest.items() if s is not None],
                "db_path": str(self.db_path),
            }

    def clear_history(self) -> None:
        """Clear in-memory history (does not affect SQLite)."""
        with self._lock:
            self._history.clear()

    def vacuum_db(self) -> None:
        """Vacuum the SQLite database to reclaim space."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("VACUUM")
            conn.commit()