"""Tests for streaming module."""

import pytest
from datetime import datetime, timezone

from guardian.streaming.config import StreamingConfig
from guardian.streaming.models import (
    MessageType, EventType, ConnectionStatusValue,
    StreamMessage, SnapshotMessage, EventMessage,
    HeartbeatMessage, FullResyncMessage,
    HeartbeatPayload, SnapshotPayload, EventPayload, FullResyncPayload,
    MessageIdProvider,
)
from guardian.streaming.replay import ReplayBuffer


class TestStreamingConfig:
    """Tests for StreamingConfig."""

    def test_defaults(self):
        cfg = StreamingConfig()
        assert cfg.enabled is True
        assert cfg.protocol == "sse"
        assert cfg.heartbeat_interval_ms == 30_000
        assert cfg.replay_buffer_size == 100
        assert cfg.send_timeout_ms == 5_000
        assert cfg.max_connections_per_ip == 10
        assert cfg.message_rate_limit == 20.0

    def test_custom_values(self):
        cfg = StreamingConfig(enabled=False, protocol="websocket", replay_buffer_size=50)
        assert cfg.enabled is False
        assert cfg.protocol == "websocket"
        assert cfg.replay_buffer_size == 50

    def test_frozen(self):
        cfg = StreamingConfig()
        with pytest.raises(Exception):
            cfg.enabled = False


class TestMessageTypes:
    """Tests for message types."""

    def test_message_type_enum(self):
        assert MessageType.SNAPSHOT.value == "snapshot"
        assert MessageType.EVENT.value == "event"
        assert MessageType.HEARTBEAT.value == "heartbeat"
        assert MessageType.FULL_RESYNC.value == "fullResyncRequired"

    def test_event_type_enum(self):
        assert EventType.CONNECTION_STATUS.value == "connectionStatus"
        assert EventType.INCIDENT_DETECTED.value == "incidentDetected"
        assert EventType.INCIDENT_CLEARED.value == "incidentCleared"
        assert EventType.MODE_CHANGED.value == "modeChanged"

    def test_connection_status_enum(self):
        assert ConnectionStatusValue.ACTIVE.value == "ACTIVE"
        assert ConnectionStatusValue.FAILED.value == "FAILED"
        assert ConnectionStatusValue.RECOVERING.value == "RECOVERING"


class TestStreamMessage:
    """Tests for StreamMessage and subclasses."""

    def test_stream_message(self):
        now = datetime.now(timezone.utc)
        msg = StreamMessage(
            type=MessageType.SNAPSHOT,
            connection_id="conn-1",
            timestamp=now,
            payload={"tier": "T1"},
        )
        assert msg.type == MessageType.SNAPSHOT
        assert msg.connection_id == "conn-1"
        assert msg.payload == {"tier": "T1"}

    def test_snapshot_message(self):
        now = datetime.now(timezone.utc)
        msg = SnapshotMessage(
            connection_id="conn-1",
            timestamp=now,
            payload={"tier": "T1", "data": {"nodes": 3}},
        )
        assert msg.type == MessageType.SNAPSHOT

    def test_event_message(self):
        now = datetime.now(timezone.utc)
        msg = EventMessage(
            connection_id="conn-1",
            timestamp=now,
            payload={"event_type": "incidentDetected", "data": {}},
        )
        assert msg.type == MessageType.EVENT

    def test_heartbeat_message(self):
        now = datetime.now(timezone.utc)
        msg = HeartbeatMessage(
            connection_id="conn-1",
            timestamp=now,
            payload={"interval_ms": 30_000, "server_time": now.isoformat()},
        )
        assert msg.type == MessageType.HEARTBEAT

    def test_full_resync_message(self):
        now = datetime.now(timezone.utc)
        msg = FullResyncMessage(
            connection_id="conn-1",
            timestamp=now,
            payload={"reason": "replay_buffer_overflow"},
        )
        assert msg.type == MessageType.FULL_RESYNC

    def test_serialization(self):
        now = datetime.now(timezone.utc)
        msg = StreamMessage(
            type=MessageType.HEARTBEAT,
            connection_id="conn-1",
            timestamp=now,
            payload={"interval_ms": 30_000},
        )
        data = msg.model_dump()
        assert data["type"] == "heartbeat"
        assert data["connection_id"] == "conn-1"


class TestMessageIdProvider:
    """Tests for MessageIdProvider."""

    def test_next(self):
        provider = MessageIdProvider(start=1)
        assert provider.next() == 1
        assert provider.next() == 2
        assert provider.next() == 3

    def test_default_start(self):
        provider = MessageIdProvider()
        assert provider.next() == 1


class TestReplayBuffer:
    """Tests for ReplayBuffer."""

    def _make_message(self, microsecond: int):
        return StreamMessage(
            type=MessageType.SNAPSHOT,
            connection_id="conn-1",
            timestamp=datetime(2026, 1, 1, 0, 0, 0, microsecond % 1000000, tzinfo=timezone.utc),
            payload={"data": microsecond},
        )

    def test_push_and_get(self):
        buf = ReplayBuffer(maxlen=10)
        buf.push(self._make_message(1000))
        buf.push(self._make_message(2000))
        buf.push(self._make_message(3000))
        assert len(buf) == 3
        # get_after(1000) returns messages with microsecond > 1000 (oldest)
        msgs = buf.get_after(1000)
        assert len(msgs) == 2

    def test_get_after_filter(self):
        buf = ReplayBuffer(maxlen=10)
        buf.push(self._make_message(1000))
        buf.push(self._make_message(2000))
        buf.push(self._make_message(3000))
        # get_after(1500) should return messages with microsecond > 1500
        msgs = buf.get_after(1500)
        assert len(msgs) == 2
        assert msgs[0].payload["data"] == 2000

    def test_get_after_none(self):
        buf = ReplayBuffer(maxlen=10)
        buf.push(self._make_message(1))
        buf.push(self._make_message(2))
        msgs = buf.get_after(100)  # Beyond buffer
        assert len(msgs) == 0

    def test_clear(self):
        buf = ReplayBuffer(maxlen=10)
        buf.push(self._make_message(1))
        buf.clear()
        assert len(buf) == 0
        assert buf.get_after(0) == []

    def test_maxlen_enforced(self):
        buf = ReplayBuffer(maxlen=3)
        for i in range(5):
            buf.push(self._make_message((i + 1) * 1000))
        assert len(buf) == 3
        # oldest microsecond is 3000, so get_after(3000) returns msgs with microsecond > 3000
        msgs = buf.get_after(3000)
        assert len(msgs) == 2  # 4000 and 5000
        data_values = [m.payload["data"] for m in msgs]
        assert data_values == [4000, 5000]

    def test_thread_safety(self):
        import threading
        buf = ReplayBuffer(maxlen=100)
        errors = []

        def pusher():
            try:
                for i in range(100):
                    buf.push(self._make_message(i))
            except Exception as e:
                errors.append(e)

        t = threading.Thread(target=pusher)
        t.start()
        t.join()
        assert len(errors) == 0
        assert len(buf) == 100
