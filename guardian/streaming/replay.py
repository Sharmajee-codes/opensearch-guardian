"""Replay buffer for SSE reconnect support.

Keeps a bounded rolling window of the most recent streaming messages so
clients that reconnect can receive missed snapshots rather than doing a
full resync.
"""
from __future__ import annotations

from collections import deque
from threading import Lock

from guardian.streaming.models import StreamMessage


class ReplayBuffer:
    """Thread-safe bounded rolling buffer of streaming messages."""

    def __init__(self, maxlen: int = 100) -> None:
        self._buffer: deque[StreamMessage] = deque(maxlen=maxlen)
        self._lock = Lock()

    def push(self, message: StreamMessage) -> None:
        with self._lock:
            self._buffer.append(message)

    def get_after(self, last_id: int) -> list[StreamMessage]:
        with self._lock:
            if not self._buffer:
                return []

            oldest_id = self._buffer[0].timestamp.microsecond
            if last_id < oldest_id:
                return []

            return [m for m in self._buffer if m.timestamp.microsecond > last_id]

    def clear(self) -> None:
        with self._lock:
            self._buffer.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._buffer)