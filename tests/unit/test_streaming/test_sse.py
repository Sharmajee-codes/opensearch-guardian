"""Tests for the SSE streaming router."""
from __future__ import annotations

from datetime import datetime, timezone
from queue import Queue
from typing import Any
from uuid import UUID

import pytest

from guardian.collectors.snapshots.store import SnapshotStore
from guardian.collectors.tiers.enums import Tier
from guardian.streaming.config import StreamingConfig
from guardian.streaming.routers.sse import StreamingRouter, create_sse_router
from guardian.streaming.models import HeartbeatMessage, MessageType, SnapshotMessage, StreamMessage
from guardian.core_types.connection_models import ConnectionProfile


@pytest.fixture
def connection() -> ConnectionProfile:
    return ConnectionProfile(
        name="test-cluster",
        opensearch_url="http://localhost:9200",
        credential_ref="test-keyring-ref",
    )


@pytest.fixture
def snapshot_store(connection: ConnectionProfile) -> SnapshotStore:
    return SnapshotStore(connection=connection)


@pytest.fixture
def config() -> StreamingConfig:
    return StreamingConfig(
        enabled=True,
        protocol="sse",
        replay_buffer_size=50,
    )


@pytest.fixture
def router(snapshot_store: SnapshotStore, config: StreamingConfig) -> Any:
    return create_sse_router(snapshot_store, config)


class TestStreamingRouter:
    def test_router_created(self, router: Any) -> None:
        assert router is not None

    def test_router_has_routes(self, router: Any) -> None:
        assert hasattr(router, "routes")
        assert len(router.routes) > 0


class TestStreamingConfig:
    def test_defaults(self) -> None:
        config = StreamingConfig()
        assert config.enabled is True
        assert config.protocol == "sse"
        assert config.heartbeat_interval_ms == 30_000
        assert config.replay_buffer_size == 100
        assert config.send_timeout_ms == 5_000
        assert config.max_connections_per_ip == 10
        assert config.message_rate_limit == 20.0

    def test_custom_values(self) -> None:
        config = StreamingConfig(
            enabled=False,
            protocol="websocket",
            heartbeat_interval_ms=10_000,
            replay_buffer_size=200,
        )
        assert config.enabled is False
        assert config.protocol == "websocket"
        assert config.heartbeat_interval_ms == 10_000
        assert config.replay_buffer_size == 200


class TestReplayBuffer:
    def test_push_and_len(self) -> None:
        """Test that messages can be pushed and length tracked."""
        from guardian.streaming.replay import ReplayBuffer

        buffer = ReplayBuffer(maxlen=10)
        msg = StreamMessage(
            type=MessageType.SNAPSHOT,
            connection_id="test-conn",
            timestamp=datetime.now(timezone.utc),
            payload={},
        )
        buffer.push(msg)
        assert len(buffer) == 1

    def test_buffer_overflow(self) -> None:
        """Test that buffer respects maxlen."""
        from guardian.streaming.replay import ReplayBuffer

        buffer = ReplayBuffer(maxlen=5)
        for i in range(10):
            msg = StreamMessage(
                type=MessageType.SNAPSHOT,
                connection_id="test-conn",
                timestamp=datetime.now(timezone.utc),
                payload={"i": i},
            )
            buffer.push(msg)

        assert len(buffer) == 5

    def test_get_after_filtering(self) -> None:
        """Test that get_after filters correctly."""
        from guardian.streaming.replay import ReplayBuffer

        buffer = ReplayBuffer(maxlen=100)
        base_time = datetime(2026, 8, 20, 12, 0, 0, tzinfo=timezone.utc)

        for i in range(5):
            msg = StreamMessage(
                type=MessageType.SNAPSHOT,
                connection_id="test-conn",
                timestamp=base_time.replace(microsecond=i * 1000),
                payload={"i": i},
            )
            buffer.push(msg)

        # Get messages after microsecond 2000
        result = buffer.get_after(base_time.replace(microsecond=2000).microsecond)
        assert len(result) == 2  # Should get messages 3 and 4


class TestModels:
    def test_stream_message(self) -> None:
        msg = StreamMessage(
            type=MessageType.SNAPSHOT,
            connection_id="test-conn",
            timestamp=datetime.now(timezone.utc),
            payload={"tier": "t1"},
        )
        assert msg.type == MessageType.SNAPSHOT
        assert msg.connection_id == "test-conn"
        assert "payload" in msg.model_dump()

    def test_snapshot_message(self) -> None:
        payload = SnapshotMessage(
            type=MessageType.SNAPSHOT,
            connection_id="test-conn",
            timestamp=datetime.now(timezone.utc),
            payload={
                "tier": "t1",
                "data": {"status": "green"},
                "snapshot_id": "snap-123",
                "collected_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert payload.type == MessageType.SNAPSHOT
        assert payload.payload["tier"] == "t1"

    def test_heartbeat_message(self) -> None:
        msg = HeartbeatMessage(
            type=MessageType.HEARTBEAT,
            connection_id="test-conn",
            timestamp=datetime.now(timezone.utc),
            payload={"interval_ms": 30000},
        )
        assert msg.type == MessageType.HEARTBEAT

    def test_message_id_provider(self) -> None:
        from guardian.streaming.models import MessageIdProvider

        provider = MessageIdProvider(start=1)
        assert provider.next() == 1
        assert provider.next() == 2
        assert provider.next() == 3


class TestWebSocketRouter:
    def test_router_created(self, snapshot_store: SnapshotStore) -> None:
        from guardian.streaming.routers.websocket import WebSocketRouter

        router = WebSocketRouter(snapshot_store=snapshot_store)
        assert router is not None
        assert router._router is not None