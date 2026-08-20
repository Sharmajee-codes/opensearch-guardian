"""Rule-Based Planner — deterministic planning engine with no external dependencies.

Composes plan and capacity findings from deterministic rules using
CapacityPlanner, TrendAnalyzer, and OptimizationEngine outputs.
Produces typed, auditable plan entries with safety classification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from guardian.optimizer import (
    CapacityAnalysisResult,
    OptimizationEngine,
    OptimizationResult,
    OptimizerConfig,
)
from guardian.planner.planner import (
    CapacityPlanner,
    ProjectionConfig,
    ProjectionWindow,
    SizingRecommendation,
    UtilizationProjection,
)


class PlanAction(str, Enum):
    """Typed actions the planner can recommend."""

    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    RIGHT_SIZE = "right_size"
    RECLAIM_STORAGE = "reclaim_storage"
    OPTIMIZE_SHARDS = "optimize_shards"
    OPTIMIZE_REPLICAS = "optimize_replicas"
    OPTIMIZE_MAPPINGS = "optimize_mappings"
    CAPACITY_RECOVERY = "capacity_recovery"
    NO_ACTION = "no_action"


@dataclass
class PlanRule:
    """A single deterministic planning rule."""

    name: str
    description: str
    condition: str  # Human-readable condition description
    action: PlanAction
    priority: int = 50  # Lower = higher priority (1-100)
    rationale: list[str] = field(default_factory=list)


@dataclass
class PlannedAction:
    """A single recommended action from the planner."""

    action: PlanAction
    summary: str
    rationale: list[str]
    safety_tier: str  # INFORMATIONAL, SAFE_REVERSIBLE, APPROVAL_REQUIRED, DESTRUCTIVE
    priority: int
    estimated_impact: str
    confidence: float
    recommended_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class RuleBasedPlan:
    """Complete deterministic plan output."""

    plan_summary: str
    actions: list[PlannedAction]
    capacity_projections: list[dict[str, Any]]
    sizing_recommendation: dict[str, Any]
    optimizer_excerpt: dict[str, Any]
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    planner_version: str = "rule-based-v1"

    def sorted_actions(self) -> list[PlannedAction]:
        """Return actions sorted by priority (highest priority first)."""
        return sorted(self.actions, key=lambda a: (a.priority, -len(a.rationale)))

    def highest_priority_action(self) -> PlannedAction | None:
        """Return the highest priority action, or None if no actions."""
        sorted_actions = self.sorted_actions()
        return sorted_actions[0] if sorted_actions else None


class RuleBasedPlanner:
    """Deterministic planner that composes plan recommendations from rules.

    Uses existing analysis components:
    - CapacityPlanner for utilization projections and sizing recommendations
    - OptimizationEngine for optimization findings
    - TrendAnalyzer for historical trend analysis

    Produces a sorted list of PlannedAction entries with safety classification.
    """

    def __init__(
        self,
        config: ProjectionConfig | None = None,
        optimizer_config: OptimizerConfig | None = None,
    ) -> None:
        self.config = config or ProjectionConfig()
        self.optimizer_config = optimizer_config or OptimizerConfig()
        self.capacity_planner = CapacityPlanner(self.config)
        self.optimizer_engine = OptimizationEngine(self.optimizer_config)
        self._rules: list[PlanRule] = []
        self._load_default_rules()

    def _load_default_rules(self) -> None:
        """Load the default deterministic rule set."""
        self._rules = [
            PlanRule(
                name="critical_capacity",
                description="Projected utilization exceeds 100% in projection window",
                condition="projected_value > 1.0",
                action=PlanAction.SCALE_UP,
                priority=1,
                rationale=[],
            ),
            PlanRule(
                name="high_capacity",
                description="Projected utilization exceeds 85% in projection window",
                condition="projected_value > 0.85",
                action=PlanAction.SCALE_UP,
                priority=5,
                rationale=[],
            ),
            PlanRule(
                name="over_provisioned",
                description="Projected utilization below 40% and current nodes exceed minimum",
                condition="projected_value < 0.4 AND current_nodes > min_nodes",
                action=PlanAction.SCALE_DOWN,
                priority=10,
                rationale=[],
            ),
            PlanRule(
                name="reclaim_storage_threshold",
                description="Reclaimable storage exceeds 20% of cluster storage",
                condition="reclaimable_ratio > 0.20",
                action=PlanAction.RECLAIM_STORAGE,
                priority=15,
                rationale=[],
            ),
            PlanRule(
                name="shard_overhead_threshold",
                description="Average shard size exceeds 50GB",
                condition="avg_shard_size_gb > 50",
                action=PlanAction.OPTIMIZE_SHARDS,
                priority=20,
                rationale=[],
            ),
            PlanRule(
                name="replica_high_storage",
                description="High replica count with significant storage overhead",
                condition="replica_count > 2 AND storage_overhead > 0.30",
                action=PlanAction.OPTIMIZE_REPLICAS,
                priority=25,
                rationale=[],
            ),
            PlanRule(
                name="right_size_match",
                description="Current sizing is close to optimal",
                condition="sizing_confidence > 0.8 AND node_count_match",
                action=PlanAction.RIGHT_SIZE,
                priority=30,
                rationale=[],
            ),
            PlanRule(
                name="capacity_recovery_opportunity",
                description="Node identified as underutilized with recovery potential",
                condition="node_utilization < 0.4 AND recovery_potential > 0.20",
                action=PlanAction.CAPACITY_RECOVERY,
                priority=35,
                rationale=[],
            ),
            PlanRule(
                name="mapping_optimization",
                description="Mappings detected with keyword fields that could be text",
                condition="has_optimizable_mappings",
                action=PlanAction.OPTIMIZE_MAPPINGS,
                priority=50,
                rationale=[],
            ),
            PlanRule(
                name="no_action",
                description="No rule matched; current state is adequate",
                condition="default",
                action=PlanAction.NO_ACTION,
                priority=100,
                rationale=[],
            ),
        ]

    def plan(
        self,
        current_snapshot: Any,  # CollectionResult
        historical_snapshots: list[Any],  # list[CollectionResult]
        require_permission: bool = True,
    ) -> RuleBasedPlan:
        """Generate a deterministic plan from rules.

        Args:
            current_snapshot: Latest cluster snapshot
            historical_snapshots: Historical snapshots for trend analysis
            require_permission: Whether to enforce permission checks

        Returns:
            RuleBasedPlan with sorted recommended actions
        """
        # Collect all analysis inputs
        optimizer_results = self.optimizer_engine.analyze_all(
            current_snapshot, require_permission=require_permission
        )
        capacity_plan = self.capacity_planner.plan_capacity(
            current_snapshot, historical_snapshots, require_permission=require_permission
        )

        # Extract structured data from optimizer results
        optimizer_excerpt = self._extract_optimizer_findings(optimizer_results)
        capacity_projections = capacity_plan.get("projections", [])
        sizing = capacity_plan.get("sizing_recommendation", {})

        # Evaluate all rules against collected data
        candidate_actions = self._evaluate_rules(
            optimizer_excerpt=optimizer_excerpt,
            capacity_projections=capacity_projections,
            sizing=sizing,
            current_snapshot=current_snapshot,
            historical_snapshots=historical_snapshots,
        )

        # Deduplicate overlapping actions (keep highest priority per action type)
        deduped = self._deduplicate_actions(candidate_actions)

        # Build plan summary
        summary = self._build_plan_summary(deduped)

        return RuleBasedPlan(
            plan_summary=summary,
            actions=deduped,
            capacity_projections=capacity_projections,
            sizing_recommendation=sizing,
            optimizer_excerpt=optimizer_excerpt,
        )

    def _evaluate_rules(
        self,
        optimizer_excerpt: dict[str, Any],
        capacity_projections: list[dict[str, Any]],
        sizing: dict[str, Any],
        current_snapshot: Any,
        historical_snapshots: list[Any],
    ) -> list[PlannedAction]:
        """Evaluate all rules and return matching planned actions."""
        matched: list[PlannedAction] = []

        # Pre-compute common values
        combined_proj = next(
            (p for p in capacity_projections if p.get("resource") == "combined"),
            None,
        )
        projected_value = combined_proj.get("projected_value", 0.0) if combined_proj else 0.0
        current_nodes = len(current_snapshot.node_snapshots) if hasattr(current_snapshot, "node_snapshots") else 0

        # Extracted optimizer findings
        reclaimable = optimizer_excerpt.get("reclaimable_storage", [])
        shard_reduction = optimizer_excerpt.get("shard_reduction", [])
        replica_opt = optimizer_excerpt.get("replica_optimization", [])
        mapping_opt = optimizer_excerpt.get("mapping_optimization", [])
        capacity_recovery = optimizer_excerpt.get("capacity_recovery", [])

        total_store = sum(
            idx.store_size_bytes for idx in current_snapshot.index_snapshots.values()
        ) if hasattr(current_snapshot, "index_snapshots") and current_snapshot.index_snapshots else 0
        total_store_gb = total_store / (1024 ** 3) if total_store > 0 else 0

        reclaimable_gb = sum(item.get("reclaimable_bytes", 0) for item in reclaimable) / (1024 ** 3)
        reclaimable_ratio = reclaimable_gb / total_store_gb if total_store_gb > 0 else 0.0

        avg_shard_size_gb = optimizer_excerpt.get("avg_shard_size_gb", 0.0)
        replica_count = optimizer_excerpt.get("replica_count", 2)

        current_node_count = sizing.get("current_node_count", current_nodes)
        recommended_node_count = sizing.get("recommended_node_count", current_nodes)
        sizing_confidence = sizing.get("confidence", 0.5)

        # Evaluate each rule
        for rule in self._rules:
            action = self._match_rule(
                rule=rule,
                projected_value=projected_value,
                current_nodes=current_node_count,
                min_nodes=self.config.min_nodes,
                reclaimable_ratio=reclaimable_ratio,
                avg_shard_size_gb=avg_shard_size_gb,
                replica_count=replica_count,
                sizing_confidence=sizing_confidence,
                current_node_count=current_node_count,
                recommended_node_count=recommended_node_count,
                capacity_recovery=capacity_recovery,
                mapping_opt=mapping_opt,
                optimizer_excerpt=optimizer_excerpt,
            )
            if action:
                matched.append(action)

        return matched

    def _match_rule(
        self,
        rule: PlanRule,
        projected_value: float,
        current_nodes: int,
        min_nodes: int,
        reclaimable_ratio: float,
        avg_shard_size_gb: float,
        replica_count: int,
        sizing_confidence: float,
        current_node_count: int,
        recommended_node_count: int,
        capacity_recovery: list[dict[str, Any]],
        mapping_opt: list[dict[str, Any]],
        optimizer_excerpt: dict[str, Any],
    ) -> PlannedAction | None:
        """Match a single rule against computed values."""
        if rule.name == "critical_capacity":
            if projected_value > 1.0:
                return PlannedAction(
                    action=rule.action,
                    summary=f"Critical: projected combined utilization {projected_value:.1%} exceeds 100% — scale-up required",
                    rationale=[
                        f"Projected utilization: {projected_value:.1%}",
                        f"Current nodes: {current_node_count}",
                        f"Recommended nodes: {recommended_node_count}",
                        "Capacity expansion required to maintain SLA",
                    ],
                    safety_tier="APPROVAL_REQUIRED",
                    priority=rule.priority,
                    estimated_impact=f"Scale from {current_node_count} to {recommended_node_count} nodes",
                    confidence=sizing_confidence,
                )

        elif rule.name == "high_capacity":
            if projected_value > 0.85:
                return PlannedAction(
                    action=rule.action,
                    summary=f"High utilization projected: {projected_value:.1%} — plan scale-up",
                    rationale=[
                        f"Projected utilization: {projected_value:.1%}",
                        f"Current nodes: {current_node_count}",
                        "Approaching capacity limit; plan expansion",
                    ],
                    safety_tier="APPROVAL_REQUIRED",
                    priority=rule.priority,
                    estimated_impact=f"Plan scale from {current_node_count} to {recommended_node_count} nodes",
                    confidence=sizing_confidence,
                )

        elif rule.name == "over_provisioned":
            if projected_value < 0.4 and current_nodes > min_nodes:
                return PlannedAction(
                    action=rule.action,
                    summary=f"Over-provisioned: {projected_value:.1%} projected utilization with {current_nodes} nodes",
                    rationale=[
                        f"Projected utilization: {projected_value:.1%}",
                        f"Current nodes: {current_nodes} exceeds minimum ({min_nodes})",
                        "Cost optimization opportunity via scale-down",
                    ],
                    safety_tier="APPROVAL_REQUIRED",
                    priority=rule.priority,
                    estimated_impact=f"Scale down from {current_nodes} to {max(min_nodes, recommended_node_count)} nodes",
                    confidence=sizing_confidence,
                )

        elif rule.name == "reclaim_storage_threshold":
            if reclaimable_ratio > 0.20:
                return PlannedAction(
                    action=rule.action,
                    summary=f"High reclaimable storage: {reclaimable_ratio:.1%} of cluster storage",
                    rationale=[
                        f"Reclaimable storage ratio: {reclaimable_ratio:.1%}",
                        f"Reclaimable items: {len(reclaimable)}",
                        "Storage reclamation can reduce costs and improve performance",
                    ],
                    safety_tier="SAFE_REVERSIBLE",
                    priority=rule.priority,
                    estimated_impact=f"Potential {reclaimable_ratio:.1%} storage recovery",
                    confidence=0.8,
                )

        elif rule.name == "shard_overhead_threshold":
            if avg_shard_size_gb > 50:
                return PlannedAction(
                    action=rule.action,
                    summary=f"Large shards detected: average {avg_shard_size_gb:.1f}GB per shard",
                    rationale=[
                        f"Average shard size: {avg_shard_size_gb:.1f}GB",
                        "Large shards impact merge performance and recovery time",
                        "Shard splitting or index rollover recommended",
                    ],
                    safety_tier="APPROVAL_REQUIRED",
                    priority=rule.priority,
                    estimated_impact="Reduce shard sizes via splitting or rollover",
                    confidence=0.75,
                )

        elif rule.name == "replica_high_storage":
            if replica_count > 2:
                storage_overhead = 1.0 - (1.0 / replica_count)
                if storage_overhead > 0.30:
                    return PlannedAction(
                        action=rule.action,
                        summary=f"High replica count ({replica_count}) with {storage_overhead:.1%} storage overhead",
                        rationale=[
                            f"Replica count: {replica_count}",
                            f"Storage overhead: {storage_overhead:.1%}",
                            "Consider reducing replicas for less critical indices",
                        ],
                        safety_tier="APPROVAL_REQUIRED",
                        priority=rule.priority,
                        estimated_impact=f"Reduce storage overhead from {storage_overhead:.1%}",
                        confidence=0.7,
                    )

        elif rule.name == "right_size_match":
            node_count_match = current_node_count == recommended_node_count
            if sizing_confidence > 0.8 and node_count_match:
                return PlannedAction(
                    action=rule.action,
                    summary=f"Cluster is well-sized (confidence: {sizing_confidence:.1%})",
                    rationale=[
                        f"Sizing confidence: {sizing_confidence:.1%}",
                        f"Node count optimal: {current_node_count}",
                        "No action required; continue monitoring",
                    ],
                    safety_tier="INFORMATIONAL",
                    priority=rule.priority,
                    estimated_impact="None",
                    confidence=sizing_confidence,
                )

        elif rule.name == "capacity_recovery_opportunity":
            for node in capacity_recovery:
                util = node.get("current_utilization", 1.0)
                recovery_potential = node.get("recovery_potential", 0.0)
                if util < 0.4 and recovery_potential > 0.20:
                    return PlannedAction(
                        action=rule.action,
                        summary=f"Capacity recovery possible on {node.get('node_name', 'node')} "
                        f"({util:.1%} utilization)",
                        rationale=[
                            f"Node utilization: {util:.1%}",
                            f"Recovery potential: {recovery_potential:.1%}",
                            "Workload rebalancing can free capacity",
                        ],
                        safety_tier="SAFE_REVERSIBLE",
                        priority=rule.priority,
                        estimated_impact=f"Recover {recovery_potential:.1%} capacity via rebalancing",
                        confidence=0.7,
                    )

        elif rule.name == "mapping_optimization":
            if mapping_opt:
                return PlannedAction(
                    action=rule.action,
                    summary=f"Mapping optimization available for {len(mapping_opt)} indices",
                    rationale=[
                        f"Optimizable mappings: {len(mapping_opt)}",
                        "Keyword fields can be converted to text for better performance",
                    ],
                    safety_tier="APPROVAL_REQUIRED",
                    priority=rule.priority,
                    estimated_impact="Improve query performance via mapping optimization",
                    confidence=0.65,
                )

        return None

    def _extract_optimizer_findings(
        self, optimizer_results: dict[str, Any]
    ) -> dict[str, Any]:
        """Extract structured findings from optimizer results."""
        excerpt: dict[str, Any] = {
            "reclaimable_storage": [],
            "shard_reduction": [],
            "replica_optimization": [],
            "mapping_optimization": [],
            "capacity_recovery": [],
            "avg_shard_size_gb": 0.0,
            "replica_count": 2,
        }

        for key, result in optimizer_results.items():
            if not isinstance(result, dict):
                continue

            recommendations = result.get("recommendations", [])
            for rec in recommendations:
                rec_type = rec.get("type", "")
                if rec_type == "reclaimable_storage":
                    excerpt["reclaimable_storage"].append(rec)
                elif rec_type == "shard_reduction":
                    excerpt["shard_reduction"].append(rec)
                elif rec_type == "replica_optimization":
                    excerpt["replica_optimization"].append(rec)
                elif rec_type == "mapping_optimization":
                    excerpt["mapping_optimization"].append(rec)
                elif rec_type == "capacity_recovery":
                    excerpt["capacity_recovery"].append(rec)

        return excerpt

    def _deduplicate_actions(
        self, actions: list[PlannedAction]
    ) -> list[PlannedAction]:
        """Keep highest-priority action per action type."""
        best: dict[PlanAction, PlannedAction] = {}
        for action in actions:
            existing = best.get(action.action)
            if existing is None or action.priority < existing.priority:
                best[action.action] = action
        return list(best.values())

    def _build_plan_summary(self, actions: list[PlannedAction]) -> str:
        """Build a concise plan summary from sorted actions."""
        if not actions:
            return "No optimization actions required — cluster is operating normally."

        high_priority = [a for a in actions if a.priority <= 10]
        medium_priority = [a for a in actions if 10 < a.priority <= 50]

        parts = []
        if high_priority:
            parts.append(f"{len(high_priority)} high-priority action(s)")
        if medium_priority:
            parts.append(f"{len(medium_priority)} medium-priority action(s)")
        parts.append(f"Total: {len(actions)} action(s)")

        return "; ".join(parts)