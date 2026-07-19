import base64
import logging
import re
import uuid
from typing import Any, Optional

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from integrations.gmail_client import fetch_message, get_thread
from models.email_metadata import EmailMetadata
from models.thread import Thread

logger = logging.getLogger("agents.inbox_agent.reader")

CHUNK_SUMMARY_THRESHOLD = 30


class ThreadSummaryOutput(BaseModel):
    thread_summary: str = Field(description="Concise summary of the entire thread")
    key_action_items: list[str] = Field(description="List of action items detected in the thread")
    detected_deadlines: list[str] = Field(description="Any deadlines or dates mentioned")


THREAD_SUMMARY_PROMPT = """You are analyzing an email thread. Summarize the conversation, identify key action items, and extract any deadlines.

The thread contains {message_count} messages. Provide:
1. A concise summary of the entire conversation (2-3 sentences)
2. A list of action items (who needs to do what)
3. Any deadlines or important dates mentioned

Be concise and focus on actionable information.
"""


async def read_email(
    user_id: uuid.UUID,
    message_id: str,
    db: AsyncSession,
) -> dict[str, Any]:
    raw_message = await fetch_message(user_id, message_id, db)
    if not raw_message:
        return {"error": "Message not found", "message_id": message_id}

    payload = raw_message.get("payload", {})
    headers = {h["name"]: h["value"] for h in payload.get("headers", [])}

    body_text = _extract_body_text(payload)
    gmail_thread_id = raw_message.get("threadId", "")

    thread_messages = []
    if gmail_thread_id:
        try:
            thread_data = await get_thread(user_id, gmail_thread_id, db)
            thread_messages = thread_data.get("messages", [])
        except Exception as exc:
            logger.warning(f"Failed to fetch thread {gmail_thread_id}: {exc}")

    attachment_info = _extract_attachment_info(payload)

    local_metadata = await db.execute(
        select(EmailMetadata).where(
            EmailMetadata.user_id == user_id,
            EmailMetadata.gmail_message_id == message_id,
        )
    )
    ai_summary = None
    ai_metadata = local_metadata.scalar_one_or_none()
    if ai_metadata:
        ai_summary = ai_metadata.summary

    result = {
        "id": message_id,
        "thread_id": gmail_thread_id,
        "subject": headers.get("Subject", "(no subject)"),
        "from": headers.get("From", "(unknown)"),
        "to": headers.get("To", ""),
        "date": headers.get("Date", ""),
        "cc": headers.get("Cc", ""),
        "body_text": body_text[:10000] if body_text else "",
        "attachments": attachment_info,
        "ai_summary": ai_summary,
        "thread_message_count": len(thread_messages),
    }

    thread_summary_result = await summarize_thread(
        user_id, gmail_thread_id, thread_messages, db
    )
    if thread_summary_result:
        result["thread_summary"] = thread_summary_result
        result["key_action_items"] = thread_summary_result.get("key_action_items", [])
        result["detected_deadlines"] = thread_summary_result.get("detected_deadlines", [])

    return result


async def summarize_thread(
    user_id: uuid.UUID,
    gmail_thread_id: str,
    thread_messages: Optional[list[dict]] = None,
    db: Optional[AsyncSession] = None,
) -> Optional[dict[str, Any]]:
    if not gmail_thread_id:
        return None

    if thread_messages is None and db is not None:
        try:
            thread_data = await get_thread(user_id, gmail_thread_id, db)
            thread_messages = thread_data.get("messages", [])
        except Exception as exc:
            logger.warning(f"Failed to fetch thread {gmail_thread_id}: {exc}")
            return None

    if not thread_messages:
        return None

    message_count = len(thread_messages)

    if message_count <= 3:
        combined = _combine_messages_simple(thread_messages)
    elif message_count <= CHUNK_SUMMARY_THRESHOLD:
        combined = _combine_messages_simple(thread_messages)
    else:
        combined = await _hierarchical_summarize(thread_messages)

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
        api_key=settings.OPENAI_API_KEY,
    )
    structured_llm = llm.with_structured_output(ThreadSummaryOutput)

    try:
        result = await structured_llm.ainvoke([
            {"role": "system", "content": THREAD_SUMMARY_PROMPT.format(message_count=message_count)},
            {"role": "user", "content": f"Thread content:\n\n{combined[:8000]}"},
        ])
        logger.info(f"Generated thread summary for {gmail_thread_id} ({message_count} messages)")
        return result.model_dump()
    except Exception as exc:
        logger.exception(f"Thread summarization failed for {gmail_thread_id}: {exc}")
        return None


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


def _extract_attachment_info(payload: dict) -> list[dict]:
    attachments = []

    def _walk(part: dict):
        filename = part.get("filename", "")
        if filename:
            body = part.get("body", {})
            attachments.append({
                "filename": filename,
                "mime_type": part.get("mimeType", ""),
                "size": body.get("size", 0),
                "attachment_id": body.get("attachmentId", ""),
            })
        for sub in part.get("parts", []):
            _walk(sub)

    _walk(payload)
    return attachments


def _combine_messages_simple(messages: list[dict]) -> str:
    parts = []
    for idx, msg in enumerate(messages):
        payload = msg.get("payload", {})
        headers = {h["name"]: h["value"] for h in payload.get("headers", [])}
        body = _extract_body_text(payload)
        parts.append(
            f"[Message {idx + 1}]\n"
            f"From: {headers.get('From', 'unknown')}\n"
            f"Date: {headers.get('Date', 'unknown')}\n"
            f"Body: {body[:2000]}\n"
        )
    return "\n---\n".join(parts)


async def _hierarchical_summarize(messages: list[dict]) -> str:
    chunk_size = 15
    chunk_summaries = []

    for i in range(0, len(messages), chunk_size):
        chunk = messages[i:i + chunk_size]
        chunk_text = _combine_messages_simple(chunk)

        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=settings.OPENAI_API_KEY,
        )
        try:
            summary = await llm.ainvoke([
                {"role": "system", "content": "Summarize this chunk of an email thread concisely in 2-3 sentences."},
                {"role": "user", "content": chunk_text[:4000]},
            ])
            chunk_summaries.append(summary.content if hasattr(summary, "content") else str(summary))
        except Exception as exc:
            logger.warning(f"Chunk summarization failed: {exc}")
            chunk_summaries.append(f"[Chunk {i // chunk_size + 1}: {len(chunk)} messages]")

    return "\n".join(
        f"[Chunk {idx + 1} Summary] {s}"
        for idx, s in enumerate(chunk_summaries)
    )
