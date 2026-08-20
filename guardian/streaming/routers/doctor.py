"""Streaming API endpoints for real-time Doctor Rules findings.

Extends the base SSE router with Doctor Rules diagnostics integration.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from guardian.collectors.snapshots.store import SnapshotStore
from guardian.streaming.config import StreamingConfig
from guardian.streaming.diagnostics import DiagnosticEventStream
from guardian.streaming.routers.sse import StreamingRouter

logger = logging.getLogger(__name__)


class DoctorStreamingRouter(StreamingRouter):
    """SSE router with Doctor Rules diagnostics integration.

    Extends StreamingRouter to also emit diagnostic events when
    Doctor Rules produce new findings.
    """

    def __init__(
        self,
        snapshot_store: SnapshotStore,
        config: StreamingConfig | None = None,
    ) -> None:
        super().__init__(snapshot_store=snapshot_store, config=config)
        self._diag_stream = DiagnosticEventStream(streaming_router=self)

    def emit_diagnostic_events(
        self,
        findings: list[Any],
        snapshot_id: str,
        analyzed_at: datetime,
    ) -> int:
        """Emit Doctor Rules findings as streaming events.

        Returns the number of new findings emitted.
        """
        return self._diag_stream.emit_findings(findings, snapshot_id, analyzed_at)

    def emit_cleared_events(self, cleared_rules: list[str]) -> None:
        """Emit cleared/resolve events for rules."""
        self._diag_stream.emit_cleared(cleared_rules)
