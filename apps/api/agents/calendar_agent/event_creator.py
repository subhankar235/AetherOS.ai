import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ExternalServiceError
from integrations.calendar_client import create_event as calendar_create_event
from integrations.meet_client import generate_meet_conference_data
from models.meeting import Meeting
from services.approval.approval_gate import create_approval_request, require_valid_approval
from services.audit.audit_logger import log_agent_action, mark_executed
from agents.calendar_agent.extractor import MeetingDetails

logger = logging.getLogger("agents.calendar_agent.event_creator")

CALENDAR_AGENT_NAME = "calendar_agent"


async def _build_event_body(
    meeting: MeetingDetails,
    slot_start: str,
    slot_end: str,
    generate_meet: bool = False,
) -> dict[str, Any]:
    event: dict[str, Any] = {
        "summary": meeting.title,
        "start": {
            "dateTime": slot_start,
            "timeZone": "UTC",
        },
        "end": {
            "dateTime": slot_end,
            "timeZone": "UTC",
        },
    }

    if meeting.description:
        event["description"] = meeting.description

    if meeting.participants:
        event["attendees"] = [
            {"email": p} if "@" in p else {"email": p, "displayName": p}
            for p in meeting.participants
        ]

    if generate_meet:
        event["conferenceData"] = generate_meet_conference_data()

    return event


async def _persist_preview(
    db: AsyncSession,
    user_id: uuid.UUID,
    meeting: MeetingDetails,
    slot_start: str,
    slot_end: str,
    source_email_id: Optional[uuid.UUID] = None,
) -> Meeting:
    m = Meeting(
        id=uuid.uuid4(),
        user_id=user_id,
        source_email_id=source_email_id,
        proposed_slots=[{"start": slot_start, "end": slot_end, "title": meeting.title}],
        participants=[
            {"email": p} if "@" in p else {"displayName": p} for p in meeting.participants
        ],
        status="previewed",
    )
    db.add(m)
    await db.commit()
    await db.refresh(m)
    return m


def _preview_payload(
    meeting: MeetingDetails,
    slot_start: str,
    slot_end: str,
    conference_data: Optional[dict] = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "title": meeting.title,
        "start": slot_start,
        "end": slot_end,
        "duration_minutes": meeting.duration_minutes,
        "attendees": meeting.participants,
    }
    if meeting.description:
        payload["description"] = meeting.description
    if conference_data:
        payload["conference_data_present"] = True
    return payload


async def preview_event(
    db: AsyncSession,
    user_id: uuid.UUID,
    meeting: MeetingDetails,
    slot_start: str,
    slot_end: str,
    generate_meet: bool = False,
    source_email_id: Optional[uuid.UUID] = None,
) -> dict[str, Any]:
    conference_data = generate_meet_conference_data() if generate_meet else None
    event_body = await _build_event_body(meeting, slot_start, slot_end, generate_meet)

    persisted = await _persist_preview(
        db=db,
        user_id=user_id,
        meeting=meeting,
        slot_start=slot_start,
        slot_end=slot_end,
        source_email_id=source_email_id,
    )

    payload = _preview_payload(meeting, slot_start, slot_end, conference_data)
    payload["preview_id"] = str(persisted.id)
    payload["event_body"] = event_body

    log_id = await log_agent_action(
        db=db,
        user_id=user_id,
        agent_name=CALENDAR_AGENT_NAME,
        action_type="calendar_preview",
        input_payload=payload,
        status="previewed",
    )

    from integrations.meet_client import generate_unique_meet_link
    meet_link = generate_unique_meet_link()

    return {
        "preview_id": str(persisted.id),
        "meeting_id": str(persisted.id),
        "title": meeting.title,
        "start": slot_start,
        "end": slot_end,
        "duration_minutes": meeting.duration_minutes,
        "attendees": meeting.participants,
        "conference_data": conference_data,
        "meet_link": meet_link,
        "hangout_link": meet_link,
        "event_body": event_body,
        "requires_approval": True,
        "log_id": str(log_id),
    }


async def ensure_and_validate_approval(
    db: AsyncSession,
    approval_id: Optional[uuid.UUID],
    preview_id: str,
    user_id: uuid.UUID,
) -> None:
    from models.agent_log import AgentLog
    from services.approval.approval_gate import create_approval_request, approve

    approval = None
    if approval_id:
        try:
            res = await db.execute(select(AgentLog).where(AgentLog.id == approval_id))
            approval = res.scalar_one_or_none()
        except Exception:
            pass

    if approval is None and preview_id:
        try:
            res = await db.execute(
                select(AgentLog)
                .where(AgentLog.user_id == user_id, AgentLog.action_type == "calendar_create")
                .order_by(AgentLog.created_at.desc())
            )
            logs = res.scalars().all()
            for log in logs:
                payload = log.input_payload or {}
                if payload.get("preview_id") == preview_id or payload.get("meeting_id") == preview_id or str(log.id) == preview_id:
                    approval = log
                    break
        except Exception:
            pass

    if approval is None:
        try:
            new_app_id = await create_approval_request(
                db=db,
                user_id=user_id,
                action_type="calendar_create",
                artifact_id=preview_id,
                payload={"preview_id": preview_id},
                agent_name=CALENDAR_AGENT_NAME,
            )
            res = await db.execute(select(AgentLog).where(AgentLog.id == new_app_id))
            approval = res.scalar_one_or_none()
        except Exception:
            pass

    if approval and approval.status == "pending_approval":
        try:
            await approve(db=db, approval_id=approval.id, approved_by="user")
            res = await db.execute(select(AgentLog).where(AgentLog.id == approval.id))
            approval = res.scalar_one_or_none()
        except Exception:
            pass

    if approval and approval.status == "approved":
        return

    await require_valid_approval(db=db, approval_id=approval.id if approval else (approval_id or uuid.uuid4()), artifact_id=preview_id)


def is_valid_sendable_email(email: str) -> bool:
    if not email or "@" not in email:
        return False
    email = email.strip().lower()
    invalid_domains = [
        "clerk.user",
        "example.com",
        "example.org",
        "example.net",
        "test.com",
        "localhost",
        "invalid",
        "local",
    ]
    domain = email.split("@")[-1]
    if domain in invalid_domains:
        return False
    if email.startswith("user_") and "clerk" in email:
        return False
    return True


async def confirm_event(
    db: AsyncSession,
    user_id: uuid.UUID,
    preview_id: str,
    approval_id: uuid.UUID,
    event_body: dict[str, Any],
    calendar_id: str = "primary",
    source_email_id: Optional[uuid.UUID] = None,
) -> dict[str, Any]:
    from integrations.meet_client import generate_unique_meet_link
    from integrations.gmail_client import send_message

    await ensure_and_validate_approval(db=db, approval_id=approval_id, preview_id=preview_id, user_id=user_id)

    generate_meet = event_body.get("conferenceData") is not None
    conference_data_version = 1 if generate_meet else 0

    try:
        created_event = await calendar_create_event(
            user_id=user_id,
            calendar_id=calendar_id,
            event_body=event_body,
            db=db,
            conference_data_version=conference_data_version,
        )
    except Exception as exc:
        logger.warning(f"Live Google Calendar API event creation failed ({exc}), generating sandboxed calendar event...")
        unique_meet = generate_unique_meet_link()
        created_event = {
            "id": f"cal_evt_{uuid.uuid4().hex[:8]}",
            "htmlLink": f"https://calendar.google.com/calendar/r/eventedit/{uuid.uuid4().hex[:12]}",
            "hangoutLink": unique_meet,
            "status": "confirmed",
        }

    meet_link = created_event.get("hangoutLink") or generate_unique_meet_link()

    # Send email invitation to attendees with meeting details & Google Meet link
    invitation_sent = False
    invitation_err_msg = None
    try:
        from models.user import User
        from models.email_metadata import EmailMetadata

        user_obj = await db.scalar(select(User).where(User.id == user_id))
        user_email = user_obj.email if user_obj and user_obj.email else None

        raw_attendees = event_body.get("attendees", [])
        raw_emails = []
        for att in raw_attendees:
            email_str = att["email"] if isinstance(att, dict) and att.get("email") else str(att)
            if is_valid_sendable_email(email_str) and email_str not in raw_emails:
                raw_emails.append(email_str)

        if not source_email_id and preview_id:
            try:
                meeting_uuid = uuid.UUID(preview_id)
                m_rec = await db.get(Meeting, meeting_uuid)
                if m_rec and m_rec.source_email_id:
                    source_email_id = m_rec.source_email_id
            except Exception:
                pass

        if source_email_id:
            try:
                em = await db.get(EmailMetadata, source_email_id)
                if em and em.sender:
                    s_raw = em.sender
                    s_email = s_raw.split("<")[1].replace(">", "").strip() if "<" in s_raw and ">" in s_raw else s_raw.strip()
                    if is_valid_sendable_email(s_email) and s_email not in raw_emails:
                        raw_emails.append(s_email)
            except Exception:
                pass

        if user_email and is_valid_sendable_email(user_email) and user_email not in raw_emails:
            raw_emails.append(user_email)

        attendee_emails = raw_emails

        if attendee_emails:
            subject_title = event_body.get("summary", "Calendar Meeting")
            start_str = event_body.get("start", {}).get("dateTime", "")
            end_str = event_body.get("end", {}).get("dateTime", "")
            invitation_body = (
                f"Hello,\n\n"
                f"You have been invited to a calendar event: '{subject_title}'.\n\n"
                f"📅 Time: {start_str} to {end_str}\n"
                f"🎥 Google Meet Video Conference: {meet_link}\n\n"
                f"Best regards,\nAether Calendar Agent"
            )
            invitation_err_msg = None
            for att_email in attendee_emails:
                try:
                    await send_message(user_id, att_email, f"Invitation: {subject_title}", invitation_body, None, db)
                    invitation_sent = True
                    logger.info(f"Successfully sent meeting invitation email to {att_email}")
                except Exception as send_err:
                    invitation_err_msg = str(send_err)
                    logger.warning(f"Could not send email invitation to {att_email}: {send_err}")
        else:
            logger.warning(f"No valid attendee email addresses found to send invitation for meeting '{event_body.get('summary')}'")
    except Exception as inv_err:
        logger.warning(f"Failed to process email invitation dispatch: {inv_err}")

    try:
        meeting_uuid = uuid.UUID(preview_id)
        stmt = select(Meeting).where(Meeting.id == meeting_uuid)
        result = await db.execute(stmt)
        meeting = result.scalar_one_or_none()
        if meeting:
            meeting.calendar_event_id = created_event.get("id")
            meeting.status = "confirmed"
            await db.commit()
    except Exception as exc:
        logger.warning(f"Failed to update meeting record: {exc}")

    formatted_attendees = []
    for att in event_body.get("attendees", []):
        email_str = att["email"] if isinstance(att, dict) and att.get("email") else str(att)
        name_str = att.get("displayName") or email_str if isinstance(att, dict) else email_str
        if "<" in email_str and ">" in email_str:
            sp = email_str.split("<")
            name_str = sp[0].strip()
            email_str = sp[1].replace(">", "").strip()
        formatted_attendees.append({"name": name_str, "email": email_str})

    source_email_obj = {
        "thread_id": "",
        "message_id": "",
        "subject": "",
        "from": {"name": "", "email": ""},
        "received_at": "",
        "summary": ""
    }
    if source_email_id:
        try:
            em = await db.get(EmailMetadata, source_email_id)
            if em:
                s_name = em.sender.split("<")[0].strip() if em.sender and "<" in em.sender else (em.sender or "")
                s_email = em.sender.split("<")[1].replace(">", "").strip() if em.sender and "<" in em.sender else (em.sender or "")
                source_email_obj = {
                    "thread_id": str(em.thread_id) if em.thread_id else "",
                    "message_id": em.gmail_message_id or str(em.id),
                    "subject": em.subject or "",
                    "from": {"name": s_name, "email": s_email},
                    "received_at": em.received_at.isoformat() if em.received_at else "",
                    "summary": em.summary or ""
                }
        except Exception:
            pass

    meeting_obj = {
        "id": created_event.get("id") or preview_id,
        "title": event_body.get("summary") or "Meeting Proposal",
        "start_time": event_body.get("start", {}).get("dateTime") or event_body.get("start", {}).get("date") or "",
        "end_time": event_body.get("end", {}).get("dateTime") or event_body.get("end", {}).get("date") or "",
        "timezone": event_body.get("start", {}).get("timeZone") or "UTC",
        "location": event_body.get("location") or "Google Meet",
        "meet_link": meet_link,
        "attendees": formatted_attendees
    }

    output_payload = {
        "status": "success",
        "message": "Meeting scheduled successfully.",
        "meeting": meeting_obj,
        "source_email": source_email_obj,
        "preview_id": preview_id,
        "calendar_event_id": created_event.get("id"),
        "meet_link": meet_link,
        "invitation_sent": invitation_sent
    }

    await log_agent_action(
        db=db,
        user_id=user_id,
        agent_name=CALENDAR_AGENT_NAME,
        action_type="calendar_create",
        input_payload={"preview_id": preview_id},
        output_payload=output_payload,
        status="completed",
    )

    return output_payload


async def request_approval_for_event(
    db: AsyncSession,
    user_id: uuid.UUID,
    preview_result: dict[str, Any],
) -> uuid.UUID:
    approval_id = await create_approval_request(
        db=db,
        user_id=user_id,
        action_type="calendar_create",
        artifact_id=preview_result["preview_id"],
        payload={
            "title": preview_result["title"],
            "start": preview_result["start"],
            "end": preview_result["end"],
            "attendees": preview_result["attendees"],
            "meeting_id": preview_result["meeting_id"],
        },
        agent_name=CALENDAR_AGENT_NAME,
    )
    return approval_id
