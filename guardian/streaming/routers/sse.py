"""SSE streaming router.

Implements the primary streaming protocol from ``docs/architecture/live-monitoring.md``.
"""
from __future__ import annotations

import logging
import time
from collections import defaultdict
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from queue import Empty, Queue
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict

from guardian.collectors.snapshots.store import SnapshotStore
from guardian.collectors.tiers.enums import Tier
from guardian.streaming.config import StreamingConfig
from guardian.streaming.models import (
    MessageType,
    SnapshotMessage,
    StreamMessage,
)

logger = logging.getLogger(__name__)


class ClientSession(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    client_id: UUID
    ip: str
    last_event_id: int
    send_queue: Queue
    last_activity: float


class StreamingRouter:
    def __init__(
        self,
        snapshot_store: SnapshotStore,
        config: StreamingConfig | None = None,
    ) -> None:
        self._store = snapshot_store
        self._config = config or StreamingConfig()
        self._router = APIRouter(prefix="/api/stream", tags=["streaming"])

        self._sessions: dict[UUID, ClientSession] = {}
        self._ip_counters: dict[str, int] = defaultdict(int)

        self._replay = self._build_replay_buffer(self._config.replay_buffer_size)

        self._store.subscribe(Tier.T1, self._on_snapshot)
        self._build_routes()

    @staticmethod
    def _build_replay_buffer(maxlen: int) -> Any:
        from guardian.streaming.replay import ReplayBuffer
        return ReplayBuffer(maxlen=maxlen)

    def _emit(self, message: StreamMessage) -> None:
        self._replay.push(message)

    def _on_snapshot(self, tier: Tier, snapshot: Any) -> None:
        now = datetime.now(UTC)
        msg = SnapshotMessage(
            type=MessageType.SNAPSHOT,
            connection_id=str(self._store.connection.id),
            timestamp=now,
            payload={
                "tier": tier.value,
                "data": snapshot,
                "snapshot_id": str(uuid4()),
                "collected_at": now.isoformat(),
            },
        )
        self._emit(msg)

        for session in self._sessions.values():
            try:
                if not session.send_queue.full():
                    session.send_queue.put_nowait(msg)
            except Exception:  # noqa: BLE001
                pass

    async def _sse_iter(
        self,
        session: ClientSession,
        start_id: int,
    ) -> AsyncIterator[bytes]:
        while True:
            try:
                msg = session.send_queue.get(timeout=1.0)
            except Empty:
                yield b": keep-alive\n\n"
                continue

            if msg.timestamp.microsecond <= start_id:
                continue

            data = msg.model_dump_json()
            yield (
                f"id: {msg.timestamp.microsecond}\n"
                f"event: {msg.type.value}\n"
                f"data: {data}\n"
                "\n"
            ).encode()

    def _build_routes(self) -> None:
        @self._router.get("/sse", include_in_schema=False)
        async def stream_sse(
            request: Request,
            last_event_id: int = Query(default=0),
        ) -> StreamingResponse:
            if not self._config.enabled:
                raise RuntimeError("Streaming disabled")

            client_ip = request.client.host if request.client else "unknown"
            if self._ip_counters[client_ip] >= self._config.max_connections_per_ip:
                raise RuntimeError("Too many connections from this IP")

            client_id = uuid4()
            session = ClientSession(
                client_id=client_id,
                ip=client_ip,
                last_event_id=last_event_id,
                send_queue=Queue(maxsize=self._config.replay_buffer_size + 50),
                last_activity=time.monotonic(),
            )
            self._sessions[client_id] = session
            self._ip_counters[client_ip] += 1

            logger.info(
                "SSE connected %s from %s active=%d",
                client_id,
                client_ip,
                len(self._sessions),
            )

            try:
                return StreamingResponse(
                    self._sse_iter(session, last_event_id),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "X-Accel-Buffering": "no",
                        "Access-Control-Allow-Origin": "*",
                    },
                )
            finally:
                self._sessions.pop(client_id, None)
                self._ip_counters[client_ip] = max(
                    0, self._ip_counters[client_ip] - 1
                )
                logger.info(
                    "SSE disconnected %s active=%d",
                    client_id,
                    len(self._sessions),
                )


def create_sse_router(
    snapshot_store: SnapshotStore,
    config: StreamingConfig | None = None,
) -> APIRouter:
    streaming = StreamingRouter(snapshot_store=snapshot_store, config=config)
    return streaming._router