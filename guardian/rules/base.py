"""Base classes for Doctor rules.

This module contains the base classes for rules, findings, evidence, and configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


@dataclass(frozen=True)
class EvidenceItem:
    """Evidence linking a finding to its source data."""

    source_api: str
    field_path: str
    observed_value: Any
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class Finding:
    """Normalized output produced when a rule matches."""

    rule_id: str
    rule_name: str
    severity: str  # critical, high, medium, low
    confidence: float
    entity_type: str
    entity_id: str
    observed_value: Any
    threshold_or_expected: Any
    condition_description: str
    remediation_guidance: str
    safety_level: str
    first_seen_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_seen_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    snapshot_id: str = ""
    evidence: tuple[EvidenceItem, ...] = field(default_factory=tuple)

    def __post_init__(self):
        # Ensure first_seen_at and last_seen_at are timezone-aware
        if self.first_seen_at.tzinfo is None:
            self.first_seen_at = self.first_seen_at.replace(tzinfo=UTC)
        if self.last_seen_at.tzinfo is None:
            self.last_seen_at = self.last_seen_at.replace(tzinfo=UTC)


class Rule:
    """Base class for diagnostic rules."""

    rule_id: str = ""
    rule_name: str = ""
    severity: str = "info"
    applies_to: str = ""
    confidence: float = 0.0
    remediation: str = ""
    safety_level: str = "informational"

    def evaluate(self, snapshot: Any, config: RuleConfig) -> list[Finding]:
        """Evaluate the rule against a cluster snapshot.
        Must be implemented by subclasses.
        """
        raise NotImplementedError

    def _make_finding(
        self,
        *,
        entity_type: str,
        entity_id: str,
        observed_value: Any,
        threshold_or_expected: Any,
        condition_description: str,
        evidence: tuple[EvidenceItem, ...],
        snapshot_id: str,
        now: datetime,
    ) -> Finding:
        """Helper to create a Finding instance."""
        return Finding(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            severity=self.severity,
            confidence=self.confidence,
            entity_type=entity_type,
            entity_id=entity_id,
            observed_value=observed_value,
            threshold_or_expected=threshold_or_expected,
            condition_description=condition_description,
            remediation_guidance=self.remediation,
            safety_level=self.safety_level,
            first_seen_at=now,
            last_seen_at=now,
            snapshot_id=snapshot_id,
            evidence=evidence,
        )


class RuleConfig(BaseModel):
    """Configuration for rule thresholds and parameters."""

    # Disk thresholds
    flood_stage_threshold: float = Field(default=0.95, description="Disk usage flood stage threshold (fraction)")
    disk_high_watermark_threshold: float = Field(default=0.85, description="Disk usage high watermark threshold (fraction)")
    disk_low_watermark_threshold: float = Field(default=0.75, description="Disk usage low watermark threshold (fraction)")

    # Heap thresholds
    heap_critical_threshold: float = Field(default=0.90, description="JVM heap critical threshold (fraction)")
    heap_warning_threshold: float = Field(default=0.75, description="JVM heap warning threshold (fraction)")

    # GC thresholds
    gc_critical_threshold: float = Field(default=1000.0, description="GC pause critical milliseconds")
    gc_warning_threshold: float = Field(default=500.0, description="GC pause warning milliseconds")

    # Shard thresholds
    shard_density_threshold: float = Field(default=2000.0, description="Shard count critical threshold")

    # Thread pool thresholds
    thread_pool_queue_threshold: float = Field(default=0.90, description="Thread pool queue warning threshold (fraction)")

    # CPU thresholds
    cpu_critical_threshold: float = Field(default=0.90, description="CPU usage critical threshold (fraction)")
    cpu_warning_threshold: float = Field(default=0.80, description="CPU usage warning threshold (fraction)")

    class Config:
        extra = "forbid"