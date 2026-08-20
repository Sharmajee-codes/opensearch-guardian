"""Capacity Planner — projects future resource needs based on current trends.

Implements deterministic, evidence-first capacity planning on top of the
Cost Optimizer's analysis. No LLM involvement per design constraints.

Public surface:
* ``CapacityPlanner`` — main planner engine
* ``ProjectionConfig`` — configuration for projection windows
* ``UtilizationProjection`` — projected resource utilization over time
* ``SizingRecommendation`` — node sizing and count recommendations
"""

from .analyzer import (
    ResourceTrend,
    TrendAnalyzer,
    UtilizationTrend,
)
from .analyzer import (
    ResourceTrend,
    TrendAnalyzer,
    UtilizationTrend,
)
from .planner import (
    CapacityPlanner,
    GrowthRate,
    ProjectionConfig,
    ProjectionWindow,
    SizingRecommendation,
    UtilizationProjection,
    calculate_rightsizing,
)
from .rule_based_planner import (
    PlanAction,
    PlanRule,
    PlannedAction,
    RuleBasedPlan,
    RuleBasedPlanner,
)

__all__ = [
    "CapacityPlanner",
    "GrowthRate",
    "PlanAction",
    "PlanRule",
    "PlannedAction",
    "ProjectionConfig",
    "ProjectionWindow",
    "ResourceTrend",
    "RuleBasedPlan",
    "RuleBasedPlanner",
    "SizingRecommendation",
    "TrendAnalyzer",
    "UtilizationProjection",
    "UtilizationTrend",
    "calculate_rightsizing",
]