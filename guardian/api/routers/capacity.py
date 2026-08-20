"""Capacity planning router.

Endpoints for capacity analysis and predictive planning.
"""

from fastapi import APIRouter, Depends, HTTPException
from guardian.api.security import get_current_user, require_cluster_read

from guardian.capacity.predictive_planner import PredictiveCapacityPlanner
from guardian.security import SecurityContext

router = APIRouter()


@router.get("", tags=["capacity"], dependencies=[Depends(require_cluster_read)])
async def analyze_capacity(
    current_user: dict = Depends(get_current_user),
):
    """
    Analyze capacity trends and predictions.

    Returns predictive capacity analysis based on historical data.
    """
    connection = SecurityContext.get_connection()
    if not connection:
        raise HTTPException(status_code=400, detail="No active connection")

    try:
        # Get collector orchestrator
        orchestrator = connection.orchestrator
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Collector not active")

        # Create planner
        planner = PredictiveCapacityPlanner(
            client=orchestrator._client_factory(),
            lookback_days=30,
        )

        # Analyze capacity
        analysis = planner.analyze_capacity()

        return {
            "cluster_name": analysis["cluster_name"],
            "analysis_timestamp": analysis["analysis_timestamp"],
            "lookback_days": analysis["lookback_days"],
            "trends": {
                resource: [trend.to_dict() for trend in trends]
                for resource, trends in analysis["trends"].items()
            },
            "recommendations": [rec.to_dict() for rec in analysis["recommendations"]],
            "risk_assessment": analysis["risk_assessment"],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/{resource}", tags=["capacity"], dependencies=[Depends(require_cluster_read)])
async def get_capacity_trends(
    resource: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get trends for a specific resource type.

    Args:
        resource: Resource type (disk, heap, shards, cpu)
    """
    valid_resources = ["disk", "heap", "shards", "cpu", "indices"]
    if resource not in valid_resources:
        raise HTTPException(status_code=400, detail=f"Invalid resource type. Must be one of: {valid_resources}")

    connection = SecurityContext.get_connection()
    if not connection:
        raise HTTPException(status_code=400, detail="No active connection")

    try:
        orchestrator = connection.orchestrator
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Collector not active")

        planner = PredictiveCapacityPlanner(
            client=orchestrator._client_factory(),
            lookback_days=30,
        )

        analysis = planner.analyze_capacity()
        trends = analysis["trends"].get(resource, [])

        return {
            "resource": resource,
            "trends": [trend.to_dict() for trend in trends],
            "recommendations": [
                rec.to_dict()
                for rec in analysis["recommendations"]
                if rec.resource_type == resource
            ],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk", tags=["capacity"], dependencies=[Depends(require_cluster_read)])
async def get_capacity_risk(
    current_user: dict = Depends(get_current_user),
):
    """
    Get overall capacity risk assessment.
    """
    connection = SecurityContext.get_connection()
    if not connection:
        raise HTTPException(status_code=400, detail="No active connection")

    try:
        orchestrator = connection.orchestrator
        if not orchestrator:
            raise HTTPException(status_code=503, detail="Collector not active")

        planner = PredictiveCapacityPlanner(
            client=orchestrator._client_factory(),
            lookback_days=30,
        )

        analysis = planner.analyze_capacity()

        return {
            "risk_assessment": analysis["risk_assessment"],
            "timestamp": analysis["analysis_timestamp"],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))