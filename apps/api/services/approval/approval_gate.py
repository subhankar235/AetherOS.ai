import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ApprovalRequiredError
from models.agent_log import AgentLog

logger = logging.getLogger("services.approval.approval_gate")

DEFAULT_APPROVAL_TIMEOUT_SECONDS = 300


async def create_approval_request(
    db: AsyncSession,
    user_id: uuid.UUID,
    action_type: str,
    artifact_id: str,
    payload: Optional[dict[str, Any]] = None,
    agent_name: str = "unknown",
) -> uuid.UUID:
    approval = AgentLog(
        id=uuid.uuid4(),
        user_id=user_id,
        agent_name=agent_name,
        action_type=action_type,
        input_payload=payload or {},
        requires_approval=True,
        status="pending_approval",
    )
    db.add(approval)
    await db.commit()
    await db.refresh(approval)
    logger.info(
        f"Created approval request {approval.id} for user {user_id} "
        f"action {action_type} artifact {artifact_id}"
    )
    return approval.id


async def approve(
    db: AsyncSession,
    approval_id: uuid.UUID,
    approved_by: str,
) -> bool:
    result = await db.execute(select(AgentLog).where(AgentLog.id == approval_id))
    approval = result.scalar_one_or_none()
    if approval is None:
        raise ApprovalRequiredError(f"Approval request {approval_id} not found")
    if approval.status != "pending_approval":
        raise ApprovalRequiredError(
            f"Approval request {approval_id} has status '{approval.status}', expected 'pending_approval'"
        )
    approval.status = "approved"
    approval.approved_by = approved_by
    approval.approved_at = datetime.now(timezone.utc)
    await db.commit()
    logger.info(f"Approval request {approval_id} approved by {approved_by}")
    return True


async def reject(
    db: AsyncSession,
    approval_id: uuid.UUID,
    reason: Optional[str] = None,
) -> bool:
    result = await db.execute(select(AgentLog).where(AgentLog.id == approval_id))
    approval = result.scalar_one_or_none()
    if approval is None:
        raise ApprovalRequiredError(f"Approval request {approval_id} not found")
    if approval.status != "pending_approval":
        raise ApprovalRequiredError(
            f"Approval request {approval_id} has status '{approval.status}', expected 'pending_approval'"
        )
    approval.status = "rejected"
    if reason:
        approval.output_payload = {"rejection_reason": reason}
    await db.commit()
    logger.info(f"Approval request {approval_id} rejected: {reason}")
    return True


async def require_valid_approval(
    db: AsyncSession,
    approval_id: uuid.UUID,
    artifact_id: str,
) -> None:
    result = await db.execute(select(AgentLog).where(AgentLog.id == approval_id))
    approval = result.scalar_one_or_none()
    if approval is None:
        raise ApprovalRequiredError(
            f"No approval record found for id {approval_id}",
            details={"approval_id": str(approval_id), "artifact_id": artifact_id},
        )
    if approval.status != "approved":
        raise ApprovalRequiredError(
            f"Approval {approval_id} has status '{approval.status}', expected 'approved'",
            details={"approval_id": str(approval_id), "artifact_id": artifact_id, "status": approval.status},
        )
    if approval.approved_at is None:
        raise ApprovalRequiredError(
            f"Approval {approval_id} has status 'approved' but no approval timestamp",
            details={"approval_id": str(approval_id), "artifact_id": artifact_id},
        )
    logger.info(f"Approval {approval_id} validated for artifact {artifact_id}")
