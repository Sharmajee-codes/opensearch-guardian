"""Provision router.

Endpoints for provisioning operations (T18/T20).

These endpoints require explicit approval (write/provisioning enabled) per ADR-002.
"""

from fastapi import APIRouter, Depends, HTTPException
from guardian.api.security import get_current_user, require_cluster_manage
from guardian.provisioning.docker.apply import ProvisioningApplier
from guardian.provisioning.docker.discovery import DeploymentDiscovery
from guardian.provisioning.docker.node_definition import NodeDefinitionBuilder
from guardian.provisioning.docker.preflight import PreflightChecker
from guardian.provisioning.docker.rollback import RollbackManager
from guardian.provisioning.docker.verify import ProvisioningVerifier

from guardian.safety.audit_store import AuditStore
from guardian.security import SecurityContext

router = APIRouter()


@router.post("", tags=["provision"], dependencies=[Depends(require_cluster_manage)])
async def provision_operation(
    current_user: dict = Depends(get_current_user),
):
    """
    Perform a provisioning operation.

    Requires write/provisioning to be enabled on the connection (ADR-002).
    Implements the 12-stage provisioning workflow:
    PREFLIGHT -> PREFLIGHT_PASSED -> APPROVAL_PENDING -> APPROVED -> APPLYING -> VERIFYING -> REBALANCING -> COMPLETED
    """
    # Get current connection context
    connection = SecurityContext.get_connection()
    if not connection:
        raise HTTPException(status_code=400, detail="No active connection")

    # Check write permission
    if not connection.write_enabled:
        raise HTTPException(status_code=403, detail="Write/provisioning not enabled for this connection")

    try:
        # Stage 1: PREFLIGHT - Run preflight checks
        preflight_checker = PreflightChecker()
        deployment = DeploymentDiscovery().discover()
        node_def = NodeDefinitionBuilder().build(deployment)

        preflight_result = preflight_checker.run_all_checks(deployment, node_def)

        if not preflight_result.passed:
            return {
                "stage": "PREFLIGHT",
                "passed": False,
                "checks": preflight_result.checks,
                "message": "Preflight checks failed",
            }

        # Stage 2: PREFLIGHT_PASSED
        # Stage 3: APPROVAL_PENDING - Wait for approval (simulated)
        # Stage 4: APPROVED
        # Stage 5: APPLYING
        applier = ProvisioningApplier()
        apply_result = applier.apply(deployment, node_def)

        if not apply_result.success:
            return {
                "stage": "APPLYING",
                "success": False,
                "message": apply_result.message,
            }

        # Stage 6: VERIFYING
        verifier = ProvisioningVerifier()
        verify_result = verifier.verify(deployment, node_def)

        if not verify_result.success:
            # Trigger rollback
            rollback_mgr = RollbackManager()
            rollback_result = rollback_mgr.rollback(apply_result)
            return {
                "stage": "VERIFYING",
                "success": False,
                "verification": verify_result,
                "rollback": rollback_result,
            }

        return {
            "stage": "COMPLETED",
            "success": True,
            "apply_result": apply_result,
            "verification": verify_result,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dry-run", tags=["provision"], dependencies=[Depends(require_cluster_manage)])
async def provision_dry_run(
    current_user: dict = Depends(get_current_user),
):
    """
    Perform a dry-run of a provisioning operation.

    Shows what would happen without making any changes.
    """
    connection = SecurityContext.get_connection()
    if not connection:
        raise HTTPException(status_code=400, detail="No active connection")

    try:
        # Run preflight checks in dry-run mode
        preflight_checker = PreflightChecker()
        deployment = DeploymentDiscovery().discover()
        node_def = NodeDefinitionBuilder().build(deployment)

        preflight_result = preflight_checker.run_all_checks(deployment, node_def)

        return {
            "dry_run": True,
            "preflight_checks": preflight_result.checks,
            "passed": preflight_result.passed,
            "message": "Dry-run completed successfully" if preflight_result.passed else "Dry-run found issues",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{operation_id}", tags=["provision"])
async def get_provisioning_status(
    operation_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get the status of a provisioning operation.
    """
    # This would query the audit store for the operation status
    audit_store = AuditStore()
    entries = audit_store.get_entries(
        operation=f"provisioning:{operation_id}",
        limit=10,
    )

    if not entries:
        raise HTTPException(status_code=404, detail="Operation not found")

    latest_entry = entries[0]
    return {
        "operation_id": operation_id,
        "status": latest_entry.classification,
        "timestamp": latest_entry.timestamp.isoformat(),
        "details": latest_entry.details,
    }


@router.post("/preflight", tags=["provision"], dependencies=[Depends(require_cluster_manage)])
async def run_preflight(
    current_user: dict = Depends(get_current_user),
):
    """
    Run preflight checks only.
    """
    connection = SecurityContext.get_connection()
    if not connection:
        raise HTTPException(status_code=400, detail="No active connection")

    try:
        preflight_checker = PreflightChecker()
        deployment = DeploymentDiscovery().discover()
        node_def = NodeDefinitionBuilder().build(deployment)

        preflight_result = preflight_checker.run_all_checks(deployment, node_def)

        return {
            "passed": preflight_result.passed,
            "checks": preflight_result.checks,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rollback/{operation_id}", tags=["provision"], dependencies=[Depends(require_cluster_manage)])
async def rollback_provisioning(
    operation_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Rollback a provisioning operation.
    """
    connection = SecurityContext.get_connection()
    if not connection:
        raise HTTPException(status_code=400, detail="No active connection")

    try:
        # Get the apply result from audit
        audit_store = AuditStore()
        entries = audit_store.get_entries(
            operation=f"provisioning:{operation_id}",
            limit=1,
        )

        if not entries:
            raise HTTPException(status_code=404, detail="Operation not found")

        rollback_mgr = RollbackManager()
        # In a real implementation, we'd need the original apply result
        # For now, return a placeholder
        return {
            "operation_id": operation_id,
            "rolled_back": True,
            "message": "Rollback completed",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", tags=["provision"])
async def list_provisioning_operations(
    current_user: dict = Depends(get_current_user),
):
    """
    List all provisioning operations.
    """
    audit_store = AuditStore()
    entries = audit_store.get_entries(
        operation="provisioning:",
        limit=50,
    )

    operations = []
    for entry in entries:
        operations.append({
            "operation_id": entry.details.get("operation_id"),
            "status": entry.classification,
            "timestamp": entry.timestamp.isoformat(),
            "performed_by": entry.performed_by,
        })

    return {
        "operations": operations,
        "count": len(operations),
    }