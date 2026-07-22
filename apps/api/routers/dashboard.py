import logging
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user
from db.session import get_db
from models.user import User
from models.email_metadata import EmailMetadata
from models.meeting import Meeting
from models.agent_log import AgentLog

logger = logging.getLogger("routers.dashboard")

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def dashboard_summary(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = user.id

    try:
        new_count = await db.scalar(
            select(func.count(EmailMetadata.id))
            .where(EmailMetadata.user_id == user_id)
        )

        if not new_count:
            total_db_count = await db.scalar(select(func.count(EmailMetadata.id)))
            if total_db_count:
                new_count = total_db_count
                high_priority_count = await db.scalar(
                    select(func.count(EmailMetadata.id)).where(EmailMetadata.priority == "High")
                )
                unread_count = total_db_count
            else:
                high_priority_count = 0
                unread_count = 0
        else:
            high_priority_count = await db.scalar(
                select(func.count(EmailMetadata.id))
                .where(EmailMetadata.user_id == user_id)
                .where(EmailMetadata.priority == "High")
            )
            unread_count = new_count

        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        recent_meetings = await db.scalar(
            select(func.count(Meeting.id))
            .where(Meeting.created_at >= thirty_days_ago)
        )

        pending_replies = await db.scalar(
            select(func.count(AgentLog.id))
            .where(AgentLog.status == "pending_approval")
        )

        return {
            "total_emails": new_count or 0,
            "high_priority": high_priority_count or 0,
            "unread": unread_count or 0,
            "recent_meetings": recent_meetings or 0,
            "pending_approvals": pending_replies or 0,
        }

    except Exception as e:
        logger.error(f"Failed to build dashboard summary for user {user_id}: {e}")
        return {
            "total_emails": 0,
            "high_priority": 0,
            "unread": 0,
            "recent_meetings": 0,
            "pending_approvals": 0,
        }
