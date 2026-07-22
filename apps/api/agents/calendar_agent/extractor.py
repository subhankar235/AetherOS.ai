import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from core.config import settings
from core.exceptions import ExternalServiceError
from agents.supervisor.prompts import INJECTION_GUARDRAIL

logger = logging.getLogger("agents.calendar_agent.extractor")

BUSINESS_HOUR_START = 9
BUSINESS_HOUR_END = 17
DEFAULT_DURATION_MINUTES = 60
LOOK_AHEAD_DAYS = 14


class MeetingDetails(BaseModel):
    title: str = Field(description="Meeting title or subject")
    date: Optional[str] = Field(None, description="Proposed date in YYYY-MM-DD format, or null if not specified")
    time: Optional[str] = Field(None, description="Proposed time in HH:MM (24h) format, or null if not specified")
    duration_minutes: int = Field(default=DEFAULT_DURATION_MINUTES, description="Meeting duration in minutes")
    participants: list[str] = Field(default_factory=list, description="List of participant email addresses or names")
    description: Optional[str] = Field(None, description="Meeting description or agenda")
    source_is_ambiguous: bool = Field(default=False, description="Whether the date/time/participants were ambiguous")


EXTRACTION_PROMPT = """Extract meeting scheduling details from the user's request or email content.

If the user said something like "schedule a meeting" without specifics:
- Leave date/time as null (the system will propose available slots)
- Use a reasonable default duration (60 minutes)
- Extract any participants mentioned

If the user is referencing an email that contains a meeting request, extract the proposed details.

Current date and time (UTC): {current_datetime}
User's timezone: {timezone}

""" + INJECTION_GUARDRAIL


async def extract_meeting_details(
    user_input: str,
    user_timezone: str = "UTC",
    email_context: Optional[str] = None,
    llm: Optional[ChatOpenAI] = None,
) -> MeetingDetails:
    if llm is None:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=settings.OPENAI_API_KEY,
        )

    now = datetime.now(timezone.utc)
    current_datetime = now.strftime("%Y-%m-%d %H:%M UTC")

    prompt_parts = [f"User request: {user_input}"]
    if email_context:
        prompt_parts.append(f"Email context:\n{email_context[:3000]}")

    structured_llm = llm.with_structured_output(MeetingDetails)

    try:
        result = await structured_llm.ainvoke([
            {
                "role": "system",
                "content": EXTRACTION_PROMPT.format(
                    current_datetime=current_datetime,
                    timezone=user_timezone,
                ),
            },
            {"role": "user", "content": "\n\n".join(prompt_parts)},
        ])
        logger.info(
            f"Extracted meeting: title='{result.title}', date={result.date}, "
            f"time={result.time}, duration={result.duration_minutes}, "
            f"participants={result.participants}"
        )
        return result
    except Exception as exc:
        logger.exception(f"Meeting details extraction failed: {exc}")
        raise ExternalServiceError(f"Failed to parse meeting request: {str(exc)}")


def build_search_windows(
    preferred_date: Optional[str] = None,
    preferred_time: Optional[str] = None,
    timezone_str: str = "UTC",
    look_ahead_days: int = LOOK_AHEAD_DAYS,
) -> list[dict[str, datetime]]:
    now = datetime.now(timezone.utc)

    if preferred_date:
        try:
            base = datetime.strptime(preferred_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if base < now:
                base = now
            windows = []
            if preferred_time:
                try:
                    hour, minute = map(int, preferred_time.split(":"))
                    day_start = base.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if day_start < now:
                        day_start = now
                    windows.append({
                        "start": day_start,
                        "end": day_start + timedelta(hours=3),
                    })
                except ValueError:
                    pass
            if not windows:
                windows.append({
                    "start": base.replace(hour=BUSINESS_HOUR_START, minute=0, second=0, microsecond=0),
                    "end": base.replace(hour=BUSINESS_HOUR_END, minute=0, second=0, microsecond=0),
                })
            return windows
        except ValueError:
            pass

    windows = []
    for day_offset in range(look_ahead_days):
        day = now + timedelta(days=day_offset)
        day_start = day.replace(hour=BUSINESS_HOUR_START, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=BUSINESS_HOUR_END, minute=0, second=0, microsecond=0)
        if day.date() == now.date() and now > day_start:
            day_start = now
        if day_start < day_end:
            windows.append({"start": day_start, "end": day_end})

    return windows[:5]
