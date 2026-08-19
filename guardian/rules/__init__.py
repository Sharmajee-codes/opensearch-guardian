from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, ClassVar

from pydantic import BaseModel, Field


class RuleConfig(BaseModel):
    """Thresholds for all Doctor rules. Tunable without code changes."""

    disk_high_watermark_threshold: float = 0.85
    disk_low_watermark_threshold: float = 0.90
    flood_stage_threshold: float = 0.95
    heap_warning_threshold: float = 0.75
    heap_critical_threshold: float = 0.90
    shard_density_threshold: int = 300
    thread_pool_queue_threshold: float = 0.9
    tiny_shard_doc_count_threshold: int = 1000
    mapping_field_threshold: int = 10_000
    oversized_shard_bytes: int = 50 * 1024**3
    cpu_warning_threshold: float = 0.85


class EvidenceItem(BaseModel):
    """A single piece of evidence linking a Finding back to snapshot data."""

    source_api: str
    field_path: str
    observed_value: Any
    timestamp: datetime


class Finding(BaseModel):
    """A deterministic diagnostic finding produced by a rule."""

    finding_id: str = Field(default_factory=lambda: __import__("uuid").uuid4().hex[:8])
    rule_id: str
    rule_name: str
    severity: str  # "critical" | "high" | "medium" | "low" | "info"
    confidence: float = Field(ge=0.0, le=1.0)
    entity_type: str  # "cluster" | "node" | "shard" | "index" | "setting"
    entity_id: str

    observed_value: Any
    threshold_or_expected: Any
    condition_description: str

    evidence: list[EvidenceItem] = Field(default_factory=list)

    remediation_guidance: str
    safety_level: str  # "informational" | "safe_reversible" | "approval_required" | "destructive"

    first_seen_at: datetime
    last_seen_at: datetime
    resolved_at: datetime | None = None
    resolved_by_snapshot_id: str | None = None

    correlated_with: list[str] = Field(default_factory=list)
    snapshot_id: str


class Rule(ABC):
    """Base class for all Doctor rules.

    Rules are pure functions: they accept snapshot data and return findings.
    No side effects, no network calls, no LLM involvement.
    """

    rule_id: ClassVar[str]
    rule_name: ClassVar[str]
    severity: ClassVar[str]
    applies_to: ClassVar[str]
    confidence: ClassVar[float]
    remediation: ClassVar[str]
    safety_level: ClassVar[str]
    condition_description_template: ClassVar[str] = ""

    @abstractmethod
    def evaluate(self, snapshot: Any, config: RuleConfig) -> list[Finding]:
        """Run this rule against the given snapshot and config.

        Args:
            snapshot: A CollectionResult containing ClusterSnapshot,
                      NodeSnapshot, ShardState, IndexSnapshot data.
            config: RuleConfig with threshold values.

        Returns:
            A (possibly empty) list of Finding objects.
        """
        ...

    def _make_finding(
        self,
        *,
        entity_type: str,
        entity_id: str,
        observed_value: Any,
        threshold_or_expected: Any,
        condition_description: str,
        evidence: list[EvidenceItem],
        snapshot_id: str,
        now: datetime,
    ) -> Finding:
        """Helper to construct a Finding with rule metadata."""
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
            evidence=evidence,
            remediation_guidance=self.remediation,
            safety_level=self.safety_level,
            first_seen_at=now,
            last_seen_at=now,
            snapshot_id=snapshot_id,
        )
