"""WebSocket streaming router.

Optional fallback for environments that block SSE or require full duplex.
Shares the same message format as the SSE router.
"""
from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from guardian.collectors.snapshots.store import SnapshotStore
from guardian.collectors.tiers.enums import Tier
from guardian.streaming.config import StreamingConfig
from guardian.streaming.models import MessageType

logger = logging.getLogger(__name__)


class WebSocketRouter:
    """WebSocket-based streaming router.

    Simpler than SSE: no replay buffer needed since WS frames are
    reliable and in-order per connection.
    """

    def __init__(
        self,
        snapshot_store: SnapshotStore,
        config: StreamingConfig | None = None,
    ) -> None:
        self._store = snapshot_store
        self._config = config or StreamingConfig()
        self._router = APIRouter(prefix="/api/stream", tags=["streaming"])
        self._clients: dict[UUID, WebSocket] = {}
        self._ip_counters: dict[str, int] = defaultdict(int)

        self._store.subscribe(Tier.T1, self._on_snapshot)
        self._build_routes()

    def _on_snapshot(self, tier: Tier, snapshot: Any) -> None:
        now = datetime.now(UTC)
        payload = {
            "tier": tier.value,
            "data": snapshot,
            "snapshot_id": str(uuid4()),
            "collected_at": now.isoformat(),
        }
        message = {
            "type": MessageType.SNAPSHOT.value,
            "connectionId": str(self._store.connection.id),
            "timestamp": now.isoformat(),
            "payload": payload,
        }
        data = json.dumps(message, default=str)
        for client in self._clients.values():
            try:
                asyncio.get_event_loop().run_until_complete(
                    client.send_text(data)
                )
            except Exception:  # noqa: BLE001
                pass

    def _build_routes(self) -> None:
        @self._router.get("/ws")
        async def stream_ws(websocket: WebSocket) -> None:
            if not self._config.enabled:
                await websocket.close(code=1013)
                return

            ip = (
                websocket.client.host
                if websocket.client
                else "unknown"
            )
            if self._ip_counters[ip] >= self._config.max_connections_per_ip:
                await websocket.close(code=1013)
                return

            await websocket.accept()
            client_id = uuid4()
            self._clients[client_id] = websocket
            self._ip_counters[ip] += 1

            logger.info("WS connected %s from %s", client_id, ip)
            try:
                while True:
                    await websocket.receive_text()
            except WebSocketDisconnect:
                pass
            finally:
                self._clients.pop(client_id, None)
                self._ip_counters[ip] = max(
                    0, self._ip_counters[ip] - 1
                )

    def get_router(self) -> APIRouter:
        return self._router


def create_ws_router(
    snapshot_store: SnapshotStore,
    config: StreamingConfig | None = None,
) -> APIRouter:
    return WebSocketRouter(
        snapshot_store=snapshot_store,
        config=config,
    ).get_router()