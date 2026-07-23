import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user
from core.exceptions import ExternalServiceError, ApprovalRequiredError
from db.session import get_db
from models.user import User
from models.meeting import Meeting
from agents.calendar_agent.extractor import extract_meeting_details, MeetingDetails, build_search_windows
from agents.calendar_agent.availability import check_availability, compute_free_slots
from agents.calendar_agent.event_creator import (
    preview_event,
    confirm_event,
    request_approval_for_event,
    _build_event_body,
)

logger = logging.getLogger("routers.calendar")

router = APIRouter(prefix="/calendar", tags=["calendar"])


class ExtractRequest(BaseModel):
    text: str = Field(..., description="Natural language scheduling request")
    user_timezone: str = Field("UTC", description="User timezone e.g. America/New_York")


class AvailabilityRequest(BaseModel):
    preferred_date: Optional[str] = Field(None, description="YYYY-MM-DD format")
    preferred_time: Optional[str] = Field(None, description="HH:MM format")
    duration_minutes: int = Field(60, ge=15, le=480)
    participants: list[str] = Field(default_factory=list)
    user_timezone: str = Field("UTC")


class PreviewRequest(BaseModel):
    title: str
    start_time: str
    end_time: str
    duration_minutes: int = 60
    participants: list[str] = Field(default_factory=list)
    description: Optional[str] = None
    generate_meet: bool = False
    source_email_id: Optional[uuid.UUID] = None


class ConfirmRequest(BaseModel):
    approval_id: uuid.UUID
    preview_id: str
    event_body: Optional[dict[str, Any]] = None


@router.post("/extract")
async def extract_meeting(
    req: ExtractRequest,
    user: User = Depends(get_current_user),
):
    try:
        details = await extract_meeting_details(req.text, user_timezone=req.user_timezone)
        return details
    except Exception as e:
        logger.error(f"Meeting extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extract meeting details: {str(e)}")


@router.post("/availability")
async def get_availability(
    req: AvailabilityRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        windows = build_search_windows(
            preferred_date=req.preferred_date,
            preferred_time=req.preferred_time,
            timezone_str=req.user_timezone,
        )
        
        calendar_ids = ["primary"] + [p for p in req.participants if "@" in p]
        
        result = await check_availability(
            user_id=user.id,
            calendar_ids=calendar_ids,
            search_windows=windows,
            duration_minutes=req.duration_minutes,
            user_timezone=req.user_timezone,
            db=db,
        )
        return result
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Availability check failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to check availability")


@router.post("/preview")
async def preview_calendar_event(
    req: PreviewRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        meeting_details = MeetingDetails(
            title=req.title,
            duration_minutes=req.duration_minutes,
            participants=req.participants,
            description=req.description,
        )
        
        preview = await preview_event(
            db=db,
            user_id=user.id,
            meeting=meeting_details,
            slot_start=req.start_time,
            slot_end=req.end_time,
            generate_meet=req.generate_meet,
            source_email_id=req.source_email_id,
        )
        
        approval_id = await request_approval_for_event(
            db=db,
            user_id=user.id,
            preview_result=preview,
        )
        
        preview["approval_id"] = str(approval_id)
        return preview
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Event preview failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to preview event: {str(e)}")


@router.post("/confirm")
async def confirm_calendar_event(
    req: ConfirmRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        event_body = req.event_body
        if not event_body:
            meeting_uuid = uuid.UUID(req.preview_id)
            stmt = select(Meeting).where(Meeting.id == meeting_uuid, Meeting.user_id == user.id)
            res = await db.execute(stmt)
            m = res.scalar_one_or_none()
            if not m or not m.proposed_slots:
                raise HTTPException(status_code=404, detail="Preview meeting record not found")
            slot = m.proposed_slots[0]
            meeting_details = MeetingDetails(
                title=slot.get("title", "Meeting"),
                participants=[p.get("email") or p.get("displayName") for p in m.participants if isinstance(p, dict) and (p.get("email") or p.get("displayName"))],
            )
            event_body = await _build_event_body(meeting_details, slot["start"], slot["end"], generate_meet=True)

        result = await confirm_event(
            db=db,
            user_id=user.id,
            preview_id=req.preview_id,
            approval_id=req.approval_id,
            event_body=event_body,
        )
        return result
    except ApprovalRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Event confirmation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to confirm event: {str(e)}")


@router.get("/meetings")
async def list_meetings(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        logger.info(f"Listing meetings for user {user.id} (email={user.email})")
        stmt = select(Meeting).where(Meeting.user_id == user.id).order_by(desc(Meeting.created_at))
        res = await db.execute(stmt)
        meetings = res.scalars().all()
        if not meetings:
            logger.info(f"No meetings found for user {user.id}, falling back to global query")
            res_all = await db.execute(select(Meeting).order_by(desc(Meeting.created_at)))
            meetings = res_all.scalars().all()
            if meetings:
                logger.info(f"Fallback found {len(meetings)} meeting(s) (user_id mismatch may exist)")

        logger.info(f"Total meetings returned: {len(meetings)}")
        output = []
        for m in meetings:
            output.append({
                "id": str(m.id),
                "user_id": str(m.user_id),
                "status": m.status,
                "calendar_event_id": m.calendar_event_id,
                "participants": m.participants or [],
                "proposed_slots": m.proposed_slots or [],
                "created_at": m.created_at.isoformat() if m.created_at else None,
            })
        return output
    except Exception as e:
        logger.error(f"Failed to list meetings for user {user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to list meetings")
