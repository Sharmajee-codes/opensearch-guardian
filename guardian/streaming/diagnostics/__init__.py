"""Diagnostic event streaming integration.

Bridges Doctor Rules findings to the streaming layer, enabling real-time
notification of diagnostic events to connected SSE/WebSocket clients.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime, timezone
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from guardian.rules import RuleConfig

if TYPE_CHECKING:
    from guardian.collectors.snapshots.store import SnapshotStore
    from guardian.rules import Finding
    from guardian.streaming.models import StreamMessage
    from guardian.streaming.routers.sse import StreamingRouter

logger = logging.getLogger(__name__)


class DiagnosticEventStream:
    """Streams Doctor Rules findings to connected SSE/WebSocket clients.

    This class bridges the DiagnosisEngine output to the streaming layer,
    emitting events when new findings are produced or when existing findings
    are cleared.
    """

    def __init__(
        self,
        streaming_router: StreamingRouter,
        config: RuleConfig | None = None,
    ) -> None:
        self._router = streaming_router
        self._config = config or RuleConfig()
        self._previous_findings: dict[str, Finding] = {}

    def emit_findings(
        self,
        findings: list[Finding],
        snapshot_id: str,
        analyzed_at: datetime,
    ) -> int:
        """Emit diagnostic findings as streaming events.

        Returns the number of new findings emitted.
        """
        new_count = 0
        current_findings = {f.rule_id: f for f in findings}

        # Emit new and updated findings
        for rule_id, finding in current_findings.items():
            previous = self._previous_findings.get(rule_id)
            if previous is None or previous.observed_value != finding.observed_value:
                new_count += 1
                self._emit_finding_event(finding, snapshot_id, analyzed_at)

        # Update previous state
        self._previous_findings = current_findings

        return new_count

    def emit_cleared(self, cleared_rules: list[str]) -> None:
        """Emit events for cleared/resolve rules."""
        for rule_id in cleared_rules:
            self._emit_clear_event(rule_id)
            self._previous_findings.pop(rule_id, None)

    def _emit_finding_event(
        self,
        finding: Finding,
        snapshot_id: str,
        analyzed_at: datetime,
    ) -> None:
        """Format and emit a single finding as a streaming event."""
        now = datetime.now(UTC)
        msg = {
            "type": "event",
            "connectionId": "diagnostic-engine",
            "timestamp": now.isoformat(),
            "payload": {
                "eventType": "incidentDetected",
                "data": {
                    "rule_id": finding.rule_id,
                    "rule_name": finding.rule_name,
                    "severity": finding.severity,
                    "confidence": finding.confidence,
                    "entity_type": finding.entity_type,
                    "entity_id": finding.entity_id,
                    "observed_value": str(finding.observed_value),
                    "threshold_or_expected": str(finding.threshold_or_expected),
                    "condition_description": finding.condition_description,
                    "remediation_guidance": finding.remediation_guidance,
                    "snapshot_id": snapshot_id,
                    "analyzed_at": analyzed_at.isoformat(),
                    "evidence": [
                        {
                            "source_api": e.source_api,
                            "field_path": e.field_path,
                            "observed_value": str(e.observed_value),
                            "timestamp": e.timestamp.isoformat(),
                        }
                        for e in finding.evidence
                    ],
                },
            },
        }
        self._router._emit(msg)  # type: ignore[attr-defined]
        logger.debug(
            "Emitted finding event: %s (%s) for %s.%s",
            finding.rule_id,
            finding.severity,
            finding.entity_type,
            finding.entity_id,
        )

    def _emit_clear_event(self, rule_id: str) -> None:
        """Format and emit a clear/resolved event."""
        now = datetime.now(UTC)
        msg = {
            "type": "event",
            "connectionId": "diagnostic-engine",
            "timestamp": now.isoformat(),
            "payload": {
                "eventType": "incidentCleared",
                "data": {
                    "rule_id": rule_id,
                    "cleared_at": now.isoformat(),
                },
            },
        }
        self._router._emit(msg)  # type: ignore[attr-defined]
        logger.debug("Emitted clear event for rule: %s", rule_id)


def create_diagnostic_stream(
    streaming_router: StreamingRouter,
    config: RuleConfig | None = None,
) -> DiagnosticEventStream:
    """Factory function for DiagnosticEventStream."""
    return DiagnosticEventStream(
        streaming_router=streaming_router,
        config=config,
    )
