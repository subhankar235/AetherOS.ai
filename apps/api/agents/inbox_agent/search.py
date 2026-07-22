import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from integrations.gmail_client import search_messages, fetch_message, get_thread
from integrations.google_auth import get_google_credentials

logger = logging.getLogger("agents.inbox_agent.search")

DEFAULT_PAGE_SIZE = 25


class GmailQueryOutput(BaseModel):
    query: str = Field(description="The Gmail search query string")
    explanation: str = Field(description="Brief explanation of the query")


NL_SEARCH_PROMPT = """You translate natural language email queries into Gmail search syntax.

Examples:
- "emails from Sundar last week" → `from:sundar after:2025/07/12 before:2025/07/19`
- "unread high priority emails" → `is:unread label:INBOX`
- "emails with attachments from Alice" → `from:alice has:attachment`
- "meeting requests this month" → `subject:(meeting OR calendar) after:2025/07/01 before:2025/08/01`
- "show me everything from yesterday" → `after:2025/07/18 before:2025/07/19`

Rules:
- Use `from:` for sender-based queries
- Use `after:` and `before:` with YYYY/MM/DD dates
- Resolve relative time expressions (today, yesterday, last week, this month) based on the current date
- Use `subject:` for subject searches
- Use `has:attachment` for attachment searches
- Use `is:unread` for unread emails
- Keep the query concise and specific
- If the query is ambiguous, make a reasonable interpretation

Current date: {current_date}
User timezone: {timezone}
"""


async def build_gmail_query(
    natural_query: str,
    user_timezone: str = "UTC",
    llm: Optional[ChatOpenAI] = None,
) -> GmailQueryOutput:
    if llm is None:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.0,
            api_key=settings.OPENAI_API_KEY,
        )

    now = datetime.now(timezone.utc)
    current_date = now.strftime("%Y/%m/%d")

    structured_llm = llm.with_structured_output(GmailQueryOutput)

    result = await structured_llm.ainvoke([
        {"role": "system", "content": NL_SEARCH_PROMPT.format(
            current_date=current_date,
            timezone=user_timezone,
        )},
        {"role": "user", "content": natural_query},
    ])
    logger.info(f"NL search '{natural_query}' → Gmail query '{result.query}'")
    return result


async def natural_language_search(
    user_id: uuid.UUID,
    natural_query: str,
    db: AsyncSession,
    page_token: Optional[str] = None,
    page_size: int = DEFAULT_PAGE_SIZE,
    user_timezone: str = "UTC",
) -> dict[str, Any]:
    query_output = await build_gmail_query(natural_query, user_timezone)
    gmail_query = query_output.query

    gmail_result = await search_messages(user_id, gmail_query, page_token, db)
    messages = gmail_result.get("messages", [])
    next_page_token = gmail_result.get("nextPageToken")

    if not messages:
        return {
            "query": gmail_query,
            "explanation": query_output.explanation,
            "results": [],
            "total_results": 0,
            "next_page_token": None,
            "page_size": page_size,
        }

    message_ids = [m["id"] for m in messages[:page_size]]

    detailed_results = []
    for msg_id in message_ids:
        try:
            raw = await fetch_message(user_id, msg_id, db)
            payload = raw.get("payload", {})
            headers = {h["name"]: h["value"] for h in payload.get("headers", [])}
            detailed_results.append({
                "id": msg_id,
                "thread_id": raw.get("threadId", ""),
                "subject": headers.get("Subject", "(no subject)"),
                "from": headers.get("From", "(unknown)"),
                "date": headers.get("Date", ""),
                "snippet": raw.get("snippet", ""),
                "label_ids": raw.get("labelIds", []),
            })
        except Exception as exc:
            logger.warning(f"Failed to fetch message {msg_id}: {exc}")
            detailed_results.append({"id": msg_id, "error": str(exc)})

    return {
        "query": gmail_query,
        "explanation": query_output.explanation,
        "results": detailed_results,
        "total_results": len(messages),
        "next_page_token": next_page_token,
        "page_size": page_size,
    }
