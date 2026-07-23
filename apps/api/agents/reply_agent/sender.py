import json
import logging
import uuid
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import NotFoundError, ApprovalRequiredError
from integrations.gmail_client import send_message, get_thread
from integrations.google_auth import get_google_credentials
from models.draft import Draft
from models.email_metadata import EmailMetadata
from models.user import User
from services.approval.approval_gate import create_approval_request, require_valid_approval
from services.audit.audit_logger import log_agent_action

logger = logging.getLogger("agents.reply_agent.sender")


async def prepare_send(
    draft_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
    current_body_override: Optional[str] = None,
) -> dict[str, Any]:
    result = await db.execute(
        select(Draft).where(
            Draft.id == draft_id,
            Draft.user_id == user_id,
        )
    )
    draft = result.scalar_one_or_none()
    if not draft:
        raise NotFoundError(f"Draft {draft_id} not found")

    if draft.status != "drafting":
        raise ValueError(f"Draft {draft_id} has status '{draft.status}', expected 'drafting'")

    if current_body_override and current_body_override.strip() != draft.current_body.strip():
        draft.current_body = current_body_override
        await db.commit()

    email_result = await db.execute(
        select(EmailMetadata).where(EmailMetadata.id == draft.email_id)
    )
    email_meta = email_result.scalar_one_or_none()

    recipient = email_meta.sender if email_meta else "(unknown)"
    subject = email_meta.subject if email_meta else "(no subject)"
    reply_all = False

    if email_meta and email_meta.gmail_message_id:
        try:
            thread_data = await get_thread(user_id, email_meta.gmail_message_id, db)
            messages = thread_data.get("messages", [])
            if len(messages) > 1:
                prev = messages[-2] if len(messages) >= 2 else messages[-1]
                payload = prev.get("payload", {})
                headers = {h["name"]: h["value"] for h in payload.get("headers", [])}
                from_header = headers.get("From", "")
                to_header = headers.get("To", "")

                prev_from = from_header.split("<")[-1].rstrip(">") if "<" in from_header else from_header
                if to_header and len(to_header.split(",")) > 1:
                    reply_all = True
        except Exception as exc:
            logger.warning(f"Failed to analyze thread for reply-all detection: {exc}")

    subject_clean = subject
    if not subject_clean.lower().startswith("re:"):
        subject_clean = f"Re: {subject_clean}"

    confirmation = {
        "draft_id": str(draft.id),
        "recipient": recipient,
        "subject": subject_clean,
        "body": draft.current_body,
        "reply_all": reply_all,
        "email_id": str(draft.email_id) if draft.email_id else None,
        "thread_id": str(draft.thread_id) if draft.thread_id else None,
    }

    approval_id = await create_approval_request(
        db=db,
        user_id=user_id,
        action_type="send_email",
        artifact_id=str(draft.id),
        payload=confirmation,
        agent_name="reply_agent",
    )

    logger.info(f"Prepared send for draft {draft_id}, approval={approval_id}")

    return {
        "requires_approval": True,
        "approval_id": str(approval_id),
        "confirmation": confirmation,
    }


async def execute_send(
    draft_id: uuid.UUID,
    approval_id: uuid.UUID,
    user: User,
    db: AsyncSession,
) -> dict[str, Any]:
    await require_valid_approval(db, approval_id, str(draft_id))

    result = await db.execute(
        select(Draft).where(
            Draft.id == draft_id,
            Draft.user_id == user.id,
        )
    )
    draft = result.scalar_one_or_none()
    if not draft:
        raise NotFoundError(f"Draft {draft_id} not found")

    if draft.status != "drafting":
        raise ValueError(f"Draft {draft_id} has status '{draft.status}', cannot send")

    email_result = await db.execute(
        select(EmailMetadata).where(EmailMetadata.id == draft.email_id)
    )
    email_meta = email_result.scalar_one_or_none()
    if not email_meta:
        raise NotFoundError(f"Email not found for draft {draft_id}")

    recipient = email_meta.sender
    subject = email_meta.subject
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    gmail_thread_id = email_meta.gmail_message_id

    try:
        gmail_response = await send_message(
            user_id=user.id,
            to=recipient,
            subject=subject,
            body=draft.current_body,
            thread_id=gmail_thread_id,
            db=db,
        )
    except Exception as exc:
        logger.exception(f"Failed to send email for draft {draft_id}: {exc}")
        raise

    draft.status = "sent"
    await db.commit()

    await log_agent_action(
        db=db,
        user_id=user.id,
        agent_name="reply_agent",
        action_type="send_email",
        input_payload={"draft_id": str(draft_id), "recipient": recipient, "subject": subject},
        output_payload={"gmail_response_id": gmail_response.get("id", ""), "thread_id": gmail_response.get("threadId", "")},
        requires_approval=True,
        status="completed",
    )

    logger.info(f"Sent email for draft {draft_id}, gmail_id={gmail_response.get('id')}")

    return {
        "status": "sent",
        "draft_id": str(draft.id),
        "gmail_message_id": gmail_response.get("id", ""),
        "gmail_thread_id": gmail_response.get("threadId", ""),
    }
