import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user
from core.exceptions import ExternalServiceError, ApprovalRequiredError
from db.session import get_db
from models.user import User
from agents.calendar_agent import extract_meeting_details, check_availability, compute_free_slots, preview_event, confirm_event

logger = logging.getLogger("routers.calendar")

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.post("/extract")
async def extract_meeting(
    text: str = Form(..., description="Natural language scheduling request"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        details = await extract_meeting_details(text)
        return details
    except Exception as e:
        logger.error(f"Meeting extraction failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to extract meeting details")


@router.post("/availability")
async def get_availability(
    start: str = Form(..., description="ISO 8601 start of window"),
    end: str = Form(..., description="ISO 8601 end of window"),
    participants: Optional[str] = Form(None, description="Comma-separated email addresses"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        time_min = datetime.fromisoformat(start)
        time_max = datetime.fromisoformat(end)

        participant_list = []
        if participants:
            participant_list = [p.strip() for p in participants.split(",") if p.strip()]

        busy = await check_availability(
            user_id=user.id,
            calendar_ids=[str(user.email)] + participant_list,
            time_min=time_min,
            time_max=time_max,
            db=db,
        )

        slots = await compute_free_slots(
            user_id=user.id,
            busy_data=busy,
            time_min=time_min,
            time_max=time_max,
            db=db,
        )

        return {
            "time_min": time_min.isoformat(),
            "time_max": time_max.isoformat(),
            "busy_periods": busy,
            "free_slots": slots,
        }
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Availability check failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to check availability")


@router.post("/preview")
async def preview_calendar_event(
    title: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    participants: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    add_meet: bool = Form(False),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    participant_list = []
    if participants:
        participant_list = [p.strip() for p in participants.split(",") if p.strip()]

    try:
        preview = await preview_event(
            user_id=user.id,
            title=title,
            start_time=datetime.fromisoformat(start_time),
            end_time=datetime.fromisoformat(end_time),
            participants=participant_list,
            description=description or "",
            add_meet=add_meet,
            db=db,
        )
        return preview
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Event preview failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to preview event")


@router.post("/confirm")
async def confirm_calendar_event(
    approval_id: str = Form(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await confirm_event(
            approval_id=uuid.UUID(approval_id),
            user_id=user.id,
            db=db,
        )
        return result
    except ApprovalRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Event confirmation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to confirm event")
