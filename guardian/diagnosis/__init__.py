"""Diagnosis engine — runs all rules against snapshots and correlates findings."""

from __future__ import annotations

from datetime import UTC, datetime, timezone
from typing import Any

from ..models import CollectionResult
from ..rules import Finding, RuleConfig
from ..rules.builtin import (
    ClusterHealthRule,
    CpuSaturationRule,
    DiskWatermarkRule,
    JvmGcRule,
    JvmHeapRule,
    ReadOnlyIndexRule,
    ShardDensityRule,
    ThreadPoolQueueRule,
    ThreadPoolRejectionRule,
    UnassignedReplicaShardsRule,
    UnassignedShardsRule,
)


class DiagnosisResult:
    """Output of a diagnosis pass."""

    def __init__(
        self,
        findings: list[Finding],
        snapshot_id: str,
        analyzed_at: datetime,
    ):
        self.findings = findings
        self.snapshot_id = snapshot_id
        self.analyzed_at = analyzed_at

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "critical")

    @property
    def high_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "high")

    @property
    def medium_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "medium")

    def by_severity(self) -> dict[str, list[Finding]]:
        result: dict[str, list[Finding]] = {}
        for f in self.findings:
            result.setdefault(f.severity, []).append(f)
        return result


class DiagnosisEngine:
    """Runs Doctor rules against a CollectionResult and returns findings."""

    def __init__(self, config: RuleConfig | None = None):
        self.config = config or RuleConfig()
        self._rules: list[Any] = [
            ClusterHealthRule(),
            DiskWatermarkRule(),
            JvmHeapRule(),
            JvmGcRule(),
            ShardDensityRule(),
            ThreadPoolRejectionRule(),
            ThreadPoolQueueRule(),
            UnassignedShardsRule(),
            UnassignedReplicaShardsRule(),
            ReadOnlyIndexRule(),
            CpuSaturationRule(),
        ]

    def diagnose(self, snapshot: CollectionResult) -> DiagnosisResult:
        """Run all rules against the snapshot.

        Args:
            snapshot: A CollectionResult with cluster, node, shard, and index data.

        Returns:
            DiagnosisResult with all findings produced by the rule set.
        """
        all_findings: list[Finding] = []
        now = datetime.now(tz=UTC)
        for rule in self._rules:
            try:
                findings = rule.evaluate(snapshot, self.config)
                all_findings.extend(findings)
            except Exception as exc:
                print(f"[DiagnosisEngine] Rule {getattr(rule, 'rule_id', '?')} failed: {exc}", flush=True)
        return DiagnosisResult(
            findings=all_findings,
            snapshot_id=snapshot.cluster_snapshot.snapshot_id if snapshot.cluster_snapshot else "unknown",
            analyzed_at=now,
        )