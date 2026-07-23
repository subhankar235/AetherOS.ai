import uuid
from datetime import datetime
import logging
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from googleapiclient.discovery import build
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import settings
from core.limiter import limiter
from integrations.google_auth import get_google_credentials, GoogleScopes

logger = logging.getLogger("integrations.calendar_client")

calendar_retry = retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=1, max=3),
    reraise=True
)


async def _get_calendar_service(user_id: uuid.UUID, db: AsyncSession):
    """
    Helper to get the authorized Google Calendar API service.
    """
    creds = await get_google_credentials(user_id, db, [GoogleScopes.CALENDAR])
    return build("calendar", "v3", credentials=creds)


@calendar_retry
async def get_freebusy(
    user_id: uuid.UUID,
    calendar_ids: list[str],
    time_min: datetime,
    time_max: datetime,
    db: AsyncSession
) -> dict:
    """
    Checks free/busy status for the specified calendar IDs within the given time window.
    """
    await limiter.check_rate_limit(f"calendar:{user_id}", limit=settings.RATE_LIMIT_CALENDAR_PER_MIN, period=60)
    service = await _get_calendar_service(user_id, db)
    
    body = {
        "timeMin": time_min.isoformat(),
        "timeMax": time_max.isoformat(),
        "items": [{"id": cid} for cid in calendar_ids]
    }
    req = service.freebusy().query(body=body)
    return await asyncio.wait_for(asyncio.to_thread(req.execute), timeout=5.0)


@calendar_retry
async def create_event(
    user_id: uuid.UUID,
    calendar_id: str,
    event_body: dict,
    db: AsyncSession,
    conference_data_version: int = 0
) -> dict:
    """
    Creates a new calendar event.
    Set conference_data_version=1 to enable Google Meet generation.
    """
    await limiter.check_rate_limit(f"calendar:{user_id}", limit=settings.RATE_LIMIT_CALENDAR_PER_MIN, period=60)
    service = await _get_calendar_service(user_id, db)
    
    req = service.events().insert(
        calendarId=calendar_id,
        body=event_body,
        conferenceDataVersion=conference_data_version
    )
    return await asyncio.wait_for(asyncio.to_thread(req.execute), timeout=6.0)


@calendar_retry
async def update_event(
    user_id: uuid.UUID,
    calendar_id: str,
    event_id: str,
    event_body: dict,
    db: AsyncSession,
    conference_data_version: int = 0
) -> dict:
    """
    Updates an existing calendar event.
    """
    await limiter.check_rate_limit(f"calendar:{user_id}", limit=settings.RATE_LIMIT_CALENDAR_PER_MIN, period=60)
    service = await _get_calendar_service(user_id, db)
    
    req = service.events().update(
        calendarId=calendar_id,
        eventId=event_id,
        body=event_body,
        conferenceDataVersion=conference_data_version
    )
    return await asyncio.wait_for(asyncio.to_thread(req.execute), timeout=6.0)


@calendar_retry
async def delete_event(
    user_id: uuid.UUID,
    calendar_id: str,
    event_id: str,
    db: AsyncSession
) -> None:
    """
    Deletes a calendar event.
    """
    await limiter.check_rate_limit(f"calendar:{user_id}", limit=settings.RATE_LIMIT_CALENDAR_PER_MIN, period=60)
    service = await _get_calendar_service(user_id, db)
    
    req = service.events().delete(
        calendarId=calendar_id,
        eventId=event_id
    )
    await asyncio.wait_for(asyncio.to_thread(req.execute), timeout=5.0)
