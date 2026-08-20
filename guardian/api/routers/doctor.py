"""Doctor router.

Endpoints for running diagnostic rules against OpenSearch snapshots.
"""

from fastapi import APIRouter, Depends, HTTPException
from guardian.api.security import get_current_user, require_cluster_read

from guardian.rules import DiagnosisEngine
from guardian.rules.marketplace import RuleMarketplace
from guardian.security import SecurityContext

router = APIRouter()


@router.get("", tags=["doctor"], dependencies=[Depends(require_cluster_read)])
async def run_doctor_rules(
    current_user: dict = Depends(get_current_user),
):
    """
    Run all Doctor rules against the latest snapshot data.

    Returns diagnostic findings from the rule engine.
    This endpoint requires read access only.
    """
    connection = SecurityContext.get_connection()
    if not connection:
        raise HTTPException(status_code=400, detail="No active connection")

    try:
        # Create diagnosis engine
        engine = DiagnosisEngine()

        # Run diagnosis
        result = engine.diagnose(connection)

        return {
            "findings": result.findings,
            "summary": {
                "total": len(result.findings),
                "critical": result.critical_count,
                "warning": result.warning_count,
                "info": result.info_count,
            },
            "timestamp": result.timestamp,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules", tags=["doctor"], dependencies=[Depends(require_cluster_read)])
async def list_doctor_rules(
    current_user: dict = Depends(get_current_user),
):
    """
    List all available Doctor rules with their metadata.

    Returns information about each rule including ID, name, severity, etc.
    """
    from guardian.rules.builtin import BUILTIN_RULES

    rules = []
    for rule in BUILTIN_RULES:
        rules.append({
            "id": rule.ID,
            "name": rule.NAME,
            "category": rule.CATEGORY,
            "severity": rule.SEVERITY,
            "description": rule.DESCRIPTION,
            "configurable": hasattr(rule, 'DEFAULT_CONFIG'),
        })

    return {
        "rules": rules,
        "count": len(rules),
    }


@router.get("/marketplace", tags=["doctor"], dependencies=[Depends(require_cluster_read)])
async def list_marketplace_rules(
    current_user: dict = Depends(get_current_user),
):
    """
    List rules available from the marketplace.
    """
    marketplace = RuleMarketplace()
    rules = marketplace.list_available_rules()

    return {
        "rules": [rule.to_dict() for rule in rules],
        "count": len(rules),
    }


@router.get("/marketplace/{rule_id}", tags=["doctor"], dependencies=[Depends(require_cluster_read)])
async def get_marketplace_rule(
    rule_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get details of a specific marketplace rule.
    """
    marketplace = RuleMarketplace()
    rule = marketplace.get_rule(rule_id)

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    return rule.to_dict()


@router.post("/marketplace/{rule_id}/install", tags=["doctor"], dependencies=[Depends(require_cluster_manage)])
async def install_marketplace_rule(
    rule_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Install a rule from the marketplace.
    """
    marketplace = RuleMarketplace()
    success = marketplace.install_rule(rule_id)

    if not success:
        raise HTTPException(status_code=400, detail="Failed to install rule")

    return {
        "rule_id": rule_id,
        "installed": True,
    }


@router.post("/marketplace/{rule_id}/uninstall", tags=["doctor"], dependencies=[Depends(require_cluster_manage)])
async def uninstall_marketplace_rule(
    rule_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Uninstall a marketplace rule.
    """
    marketplace = RuleMarketplace()
    success = marketplace.uninstall_rule(rule_id)

    if not success:
        raise HTTPException(status_code=404, detail="Rule not installed")

    return {
        "rule_id": rule_id,
        "uninstalled": True,
    }


@router.post("/rules/{rule_id}/run", tags=["doctor"], dependencies=[Depends(require_cluster_read)])
async def run_single_rule(
    rule_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Run a specific rule.
    """
    connection = SecurityContext.get_connection()
    if not connection:
        raise HTTPException(status_code=400, detail="No active connection")

    try:
        engine = DiagnosisEngine()
        findings = engine.run_rule(connection, rule_id)

        return {
            "rule_id": rule_id,
            "findings": findings,
            "count": len(findings),
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))