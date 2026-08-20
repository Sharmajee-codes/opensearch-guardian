"""Streaming message models.

Defines the wire format for all messages sent to streaming clients,
mirroring the schema from ``docs/architecture/live-monitoring.md``.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel


class MessageType(str, Enum):
    SNAPSHOT = "snapshot"
    EVENT = "event"
    HEARTBEAT = "heartbeat"
    FULL_RESYNC = "fullResyncRequired"


class EventType(str, Enum):
    CONNECTION_STATUS = "connectionStatus"
    INCIDENT_DETECTED = "incidentDetected"
    INCIDENT_CLEARED = "incidentCleared"
    MODE_CHANGED = "modeChanged"


class ConnectionStatusValue(str, Enum):
    ACTIVE = "ACTIVE"
    FAILED = "FAILED"
    RECOVERING = "RECOVERING"


# ---------------------------------------------------------------------------
# Payloads
# ---------------------------------------------------------------------------


class HeartbeatPayload(BaseModel):
    interval_ms: int = 30_000
    server_time: datetime


class SnapshotPayload(BaseModel):
    tier: str
    data: Any
    snapshot_id: str
    collected_at: datetime


class EventPayload(BaseModel):
    event_type: str
    data: dict[str, Any]


class FullResyncPayload(BaseModel):
    reason: str = "replay_buffer_overflow"
    reconnect_after_ms: int = 1_000


# ---------------------------------------------------------------------------
# Envelope
# ---------------------------------------------------------------------------


class StreamMessage(BaseModel):
    """Single streaming message envelope."""

    type: MessageType
    connection_id: str
    timestamp: datetime
    payload: dict[str, Any]


class SnapshotMessage(StreamMessage):
    type: MessageType = MessageType.SNAPSHOT
    payload: dict[str, Any]  # SnapshotPayload shape


class EventMessage(StreamMessage):
    type: MessageType = MessageType.EVENT
    payload: dict[str, Any]  # EventPayload shape


class HeartbeatMessage(StreamMessage):
    type: MessageType = MessageType.HEARTBEAT
    payload: dict[str, Any]  # HeartbeatPayload shape


class FullResyncMessage(StreamMessage):
    type: MessageType = MessageType.FULL_RESYNC
    payload: dict[str, Any]  # FullResyncPayload shape


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class MessageIdProvider:
    """Monotonically increasing integer message IDs.

    IDs reset on *process* restart, which is acceptable for monitoring.
    """

    def __init__(self, start: int = 1) -> None:
        self._next = start

    def next(self) -> int:
        current = self._next
        self._next += 1
        return current