"""Streaming configuration.

All streaming behavior is parameterized here so operators can tune without
touching code. Values map directly to the options defined in
``docs/architecture/live-monitoring.md``.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StreamingConfig:
    """Runtime configuration for the streaming layer."""

    enabled: bool = True
    protocol: str = "sse"  # "sse" | "websocket" | "both"
    heartbeat_interval_ms: int = 30_000  # 30s
    replay_buffer_size: int = 100
    send_timeout_ms: int = 5_000  # 5s
    max_connections_per_ip: int = 10
    message_rate_limit: float = 20.0  # msgs/sec per connection; 0 = disabled