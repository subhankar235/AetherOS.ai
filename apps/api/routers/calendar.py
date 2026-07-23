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
        if req.approval_id:
            try:
                app_uuid = uuid.UUID(str(req.approval_id))
                res_app = await db.execute(select(AgentLog).where(AgentLog.id == app_uuid))
                app_rec = res_app.scalar_one_or_none()
                if app_rec and app_rec.status == "pending_approval":
                    from services.approval.approval_gate import approve
                    await approve(db=db, approval_id=app_uuid, approved_by=user.email or "user")
            except Exception as app_exc:
                logger.info(f"Auto-approval step log: {app_exc}")

        meeting_uuid = uuid.UUID(req.preview_id)
        stmt = select(Meeting).where(Meeting.id == meeting_uuid, Meeting.user_id == user.id)
        res = await db.execute(stmt)
        m = res.scalar_one_or_none()

        event_body = req.event_body
        if not event_body:
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
            approval_id=uuid.UUID(str(req.approval_id)) if req.approval_id else uuid.UUID(str(req.preview_id)),
            event_body=event_body,
            source_email_id=m.source_email_id if m else None,
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

        logger.info(f"Total meetings returned for user {user.id}: {len(meetings)}")
        output = []
        from models.email_metadata import EmailMetadata
        for m in meetings:
            slots = m.proposed_slots or []
            first_slot = slots[0] if len(slots) > 0 else {}
            from integrations.meet_client import generate_unique_meet_link
            m_link = first_slot.get("meet_link") or first_slot.get("hangout_link") or generate_unique_meet_link()

            source_email_obj = {
                "thread_id": "",
                "message_id": "",
                "subject": "",
                "from": {"name": "", "email": ""},
                "received_at": "",
                "summary": ""
            }

            if m.source_email_id:
                em = await db.get(EmailMetadata, m.source_email_id)
                if em:
                    s_raw = em.sender or ""
                    s_name = s_raw
                    s_email = s_raw
                    if "<" in s_raw and ">" in s_raw:
                        sp = s_raw.split("<")
                        s_name = sp[0].strip()
                        s_email = sp[1].replace(">", "").strip()

                    source_email_obj = {
                        "thread_id": getattr(em, "thread_id", None) or "",
                        "message_id": em.gmail_message_id or str(em.id),
                        "subject": em.subject or "",
                        "from": {"name": s_name, "email": s_email},
                        "received_at": em.received_at.isoformat() if em.received_at else "",
                        "summary": em.summary or ""
                    }

            formatted_attendees = []
            for p in (m.participants or []):
                p_str = p.get("email") or p.get("displayName") if isinstance(p, dict) else str(p)
                p_name = p_str
                p_email = p_str
                if "<" in p_str and ">" in p_str:
                    sp = p_str.split("<")
                    p_name = sp[0].strip()
                    p_email = sp[1].replace(">", "").strip()
                formatted_attendees.append({"name": p_name, "email": p_email})

            meeting_obj = {
                "id": str(m.id),
                "title": first_slot.get("title") or "Meeting Proposal",
                "start_time": first_slot.get("start") or "",
                "end_time": first_slot.get("end") or "",
                "timezone": "UTC",
                "location": "Google Meet",
                "meet_link": m_link,
                "attendees": formatted_attendees,
            }

            output.append({
                "id": str(m.id),
                "user_id": str(m.user_id),
                "status": m.status,
                "calendar_event_id": m.calendar_event_id,
                "meeting": meeting_obj,
                "source_email": source_email_obj,
                "participants": m.participants or [],
                "proposed_slots": slots,
                "meet_link": m_link,
                "hangout_link": m_link,
                "target_email": {
                    "subject": source_email_obj["subject"],
                    "sender": source_email_obj["from"]["email"] or source_email_obj["from"]["name"],
                    "id": source_email_obj["message_id"],
                } if source_email_obj["subject"] else None,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            })
        return output
    except Exception as e:
        logger.error(f"Failed to list meetings for user {user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to list meetings")
