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
    from core.llm_factory import get_provider_candidates
    import json

    now = datetime.now(timezone.utc)
    current_datetime = now.strftime("%Y-%m-%d %H:%M UTC")

    prompt_parts = [f"User request: {user_input}"]
    if email_context:
        prompt_parts.append(f"Email context:\n{email_context[:3000]}")

    user_prompt_str = "\n\n".join(prompt_parts)
    sys_prompt = EXTRACTION_PROMPT.format(
        current_datetime=current_datetime,
        timezone=user_timezone,
    )

    if llm is not None:
        structured_llm = llm.with_structured_output(MeetingDetails)
        return await structured_llm.ainvoke([
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt_str},
        ])

    candidates = get_provider_candidates(is_classifier=True)
    if not candidates:
        candidates = [{
            "name": "openai",
            "model": "gpt-4o-mini",
            "api_key": settings.OPENAI_API_KEY,
            "base_url": getattr(settings, "openai_base_url", None),
        }]

    result: Optional[MeetingDetails] = None
    last_exc: Optional[Exception] = None

    for cand in candidates:
        try:
            kwargs = {
                "model": cand["model"],
                "temperature": 0.1,
                "api_key": cand["api_key"],
                "request_timeout": 5.0,
            }
            if cand.get("base_url"):
                kwargs["base_url"] = cand["base_url"]

            candidate_llm = ChatOpenAI(**kwargs)
            try:
                structured_llm = candidate_llm.with_structured_output(MeetingDetails)
                result = await structured_llm.ainvoke([
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt_str},
                ])
            except Exception as s_exc:
                logger.info(f"Structured output failed for provider '{cand['name']}': {s_exc}. Trying JSON prompt fallback...")
                json_prompt = (
                    f"{user_prompt_str}\n\n"
                    f"IMPORTANT: Respond strictly in valid JSON format:\n"
                    f'{{"title": "Meeting Title", "date": "YYYY-MM-DD or null", "time": "HH:MM or null", "duration_minutes": 60, "participants": ["email@example.com"], "description": "Agenda or null", "source_is_ambiguous": false}}'
                )
                raw_resp = await candidate_llm.ainvoke([
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": json_prompt},
                ])
                raw_content = getattr(raw_resp, "content", str(raw_resp)).strip()
                if "```json" in raw_content:
                    raw_content = raw_content.split("```json")[1].split("```")[0].strip()
                elif "```" in raw_content:
                    raw_content = raw_content.split("```")[1].split("```")[0].strip()

                parsed = json.loads(raw_content)
                result = MeetingDetails(
                    title=parsed.get("title") or user_input,
                    date=parsed.get("date"),
                    time=parsed.get("time"),
                    duration_minutes=int(parsed.get("duration_minutes", DEFAULT_DURATION_MINUTES)),
                    participants=parsed.get("participants", []),
                    description=parsed.get("description"),
                    source_is_ambiguous=bool(parsed.get("source_is_ambiguous", False)),
                )

            if result:
                if not result.title or result.title.lower() in ["meeting scheduling request", "meeting", "scheduled meeting", "calendar meeting"]:
                    if email_context and "Subject:" in email_context:
                        for line in email_context.splitlines():
                            if line.startswith("Subject:"):
                                result.title = line.replace("Subject:", "").strip()
                                break
                logger.info(
                    f"Extracted meeting via '{cand['name']}': title='{result.title}', date={result.date}, "
                    f"time={result.time}, duration={result.duration_minutes}, participants={result.participants}"
                )
                return result
        except Exception as exc:
            last_exc = exc
            logger.warning(f"Meeting details extraction attempt failed for '{cand['name']}': {exc}")

    fallback_title = user_input
    if email_context and "Subject:" in email_context:
        for line in email_context.splitlines():
            if line.startswith("Subject:"):
                fallback_title = line.replace("Subject:", "").strip()
                break

    return MeetingDetails(
        title=fallback_title or "Meeting Proposal",
        duration_minutes=60,
        participants=[],
    )

    # Fallback to heuristic defaults if all LLM attempts fail
    logger.warning(f"All LLM extraction candidates failed: {last_exc}. Falling back to default MeetingDetails.")
    import re
    emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', user_input)
    clean_title = user_input.replace("schedule", "").replace("meeting", "").strip() or "Scheduled Meeting"
    return MeetingDetails(
        title=clean_title.capitalize(),
        date=None,
        time=None,
        duration_minutes=DEFAULT_DURATION_MINUTES,
        participants=emails,
        description=user_input,
        source_is_ambiguous=True,
    )


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
