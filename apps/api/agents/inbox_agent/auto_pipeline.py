import asyncio
import base64
import email
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from typing import Literal

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import settings
from core.exceptions import ExternalServiceError
from db.session import AsyncSessionLocal
from integrations.gmail_client import fetch_message, get_thread
from models.email_metadata import EmailMetadata
from models.thread import Thread
from agents.supervisor.prompts import INJECTION_GUARDRAIL

logger = logging.getLogger("agents.inbox_agent.auto_pipeline")

EMAIL_LLM_RETRY = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)


class EmailClassification(BaseModel):
    summary: str = Field(description="A 1-2 sentence summary of the email")
    priority: Literal["High", "Medium", "Low"] = Field(description="Priority level")
    category: str = Field(description="Category: Sales, Support, Internal, Newsletter, Personal, Finance, or Other")
    urgency: bool = Field(description="Whether this email requires urgent attention")
    reply_required: bool = Field(description="Whether this email requires a reply")
    suspicious_flag: bool = Field(description="Whether this email appears suspicious or is potentially phishing")


CLASSIFICATION_SYSTEM_PROMPT = """You are an email classification assistant. Analyze the email below and produce structured output.

Categories: Sales, Support, Internal, Newsletter, Personal, Finance, Other
Priority: High (time-sensitive or from VIP/important sender), Medium (requires attention but not urgent), Low (newsletter, spam-like, informational)

""" + INJECTION_GUARDRAIL


async def process_new_email(user_id: uuid.UUID, gmail_message_id: str, db: AsyncSession) -> Optional[EmailMetadata]:
    logger.info(f"Processing new email {gmail_message_id} for user {user_id}")

    existing = await db.execute(
        select(EmailMetadata).where(
            EmailMetadata.user_id == user_id,
            EmailMetadata.gmail_message_id == gmail_message_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        logger.info(f"Email {gmail_message_id} already processed — idempotency skip")
        return None

    raw_message = await fetch_message(user_id, gmail_message_id, db)
    if not raw_message:
        logger.warning(f"Gmail message {gmail_message_id} not fetchable")
        return None

    payload = raw_message.get("payload", {})
    headers = {h["name"]: h["value"] for h in payload.get("headers", [])}

    subject = headers.get("Subject", "(no subject)")
    sender = headers.get("From", "(unknown)")
    received_at_str = headers.get("Date") or headers.get("Received", "")
    received_at = _parse_email_date(received_at_str)

    body_text = _extract_body_text(payload)
    cleaned_body = _strip_signatures_and_quotes(body_text)

    gmail_thread_id = raw_message.get("threadId", "")

    thread = await _resolve_thread(db, user_id, gmail_thread_id)

    classification = await _classify_email(subject, sender, cleaned_body)

    email_record = EmailMetadata(
        id=uuid.uuid4(),
        user_id=user_id,
        gmail_message_id=gmail_message_id,
        thread_id=thread.id if thread else None,
        sender=sender,
        subject=subject,
        summary=classification.summary,
        priority=classification.priority,
        category=classification.category,
        urgency=classification.urgency,
        reply_required=classification.reply_required,
        suspicious_flag=classification.suspicious_flag,
        received_at=received_at,
    )
    db.add(email_record)
    await db.commit()
    await db.refresh(email_record)

    logger.info(
        f"Indexed email {gmail_message_id}: priority={classification.priority} "
        f"category={classification.category} suspicious={classification.suspicious_flag}"
    )

    await _publish_dashboard_event(user_id, email_record)

    return email_record


async def process_pubsub_payload(payload: dict) -> None:
    try:
        message_data = payload.get("message", {})
        raw_data = message_data.get("data", "")
        decoded = base64.urlsafe_b64decode(raw_data).decode("utf-8")
        notification = json.loads(decoded)

        email_address = notification.get("emailAddress", "")
        history_id = notification.get("historyId", "")

        logger.info(f"PubSub notification: email={email_address}, historyId={history_id}")
        return {"email_address": email_address, "history_id": history_id}
    except Exception as exc:
        logger.exception(f"Failed to decode PubSub payload: {exc}")
        raise


def _parse_email_date(date_str: str) -> datetime:
    try:
        from email.utils import parsedate_to_datetime
        parsed = parsedate_to_datetime(date_str)
        if parsed and parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed or datetime.now(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


def _extract_body_text(payload: dict) -> str:
    text_parts = []

    def _walk(part: dict):
        mime_type = part.get("mimeType", "")
        if mime_type == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                try:
                    decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                    text_parts.append(decoded)
                except Exception:
                    pass
        elif mime_type == "text/html":
            data = part.get("body", {}).get("data", "")
            if data:
                try:
                    decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                    clean = re.sub(r"<[^>]+>", " ", decoded)
                    clean = re.sub(r"\s+", " ", clean).strip()
                    text_parts.append(clean)
                except Exception:
                    pass
        for sub in part.get("parts", []):
            _walk(sub)

    _walk(payload)
    return "\n".join(text_parts)


def _strip_signatures_and_quotes(body: str) -> str:
    lines = body.split("\n")
    cleaned = []
    for line in lines:
        if re.match(r"^>+", line):
            continue
        if re.match(r"^-{2,}\s*$", line):
            break
        if re.match(r"^_+", line):
            break
        if re.match(r"^On .+ wrote:$", line.strip()):
            break
        if re.match(r"^--\s*$", line):
            break
        if re.match(r"^Sent from .*", line.strip()):
            break
        if re.match(r"^From:.*", line.strip()):
            break
        if re.match(r"^To:.*", line.strip()):
            continue
        if re.match(r"^Subject:.*", line.strip()):
            continue
        if re.match(r"^Sent:.*", line.strip()):
            continue
        if re.match(r"^Date:.*", line.strip()):
            continue
        if re.match(r"^Reply-To:.*", line.strip()):
            continue
        cleaned.append(line)
    result = "\n".join(cleaned).strip()
    return result if result else body


@EMAIL_LLM_RETRY
async def _classify_email(subject: str, sender: str, body: str) -> EmailClassification:
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
        api_key=settings.OPENAI_API_KEY,
    )
    structured_llm = llm.with_structured_output(EmailClassification)

    content = f"Subject: {subject}\nFrom: {sender}\nBody:\n{body[:5000]}"
    result = await structured_llm.ainvoke([
        {"role": "system", "content": CLASSIFICATION_SYSTEM_PROMPT},
        {"role": "user", "content": content},
    ])
    return result


async def _resolve_thread(db: AsyncSession, user_id: uuid.UUID, gmail_thread_id: str) -> Optional[Thread]:
    result = await db.execute(
        select(Thread).where(
            Thread.user_id == user_id,
            Thread.gmail_thread_id == gmail_thread_id,
        )
    )
    thread = result.scalar_one_or_none()
    if thread is None:
        thread = Thread(
            id=uuid.uuid4(),
            user_id=user_id,
            gmail_thread_id=gmail_thread_id,
        )
        db.add(thread)
        await db.flush()
    return thread


async def _publish_dashboard_event(user_id: uuid.UUID, email: EmailMetadata) -> None:
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.REDIS_URL)
        channel = f"dashboard:{user_id}"
        event = {
            "type": "email.new",
            "email_id": str(email.id),
            "gmail_message_id": email.gmail_message_id,
            "sender": email.sender,
            "subject": email.subject,
            "priority": email.priority,
            "category": email.category,
            "urgency": email.urgency,
            "reply_required": email.reply_required,
            "suspicious_flag": email.suspicious_flag,
        }
        await r.publish(channel, json.dumps(event))
        await r.close()
        logger.debug(f"Published dashboard event to {channel}")
    except Exception as exc:
        logger.warning(f"Failed to publish dashboard event: {exc}")
