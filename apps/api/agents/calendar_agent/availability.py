import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ExternalServiceError
from integrations.calendar_client import get_freebusy
from models.meeting import Meeting

logger = logging.getLogger("agents.calendar_agent.availability")

SLOT_STEP_MINUTES = 30

TimezoneMap = dict[str, str]


def _to_tz_aware(dt: datetime, tz_name: str) -> datetime:
    try:
        import zoneinfo
        tz = zoneinfo.ZoneInfo(tz_name)
        return dt.astimezone(tz)
    except Exception:
        return dt


async def check_availability(
    user_id: uuid.UUID,
    calendar_ids: list[str],
    search_windows: list[dict[str, datetime]],
    duration_minutes: int = 60,
    user_timezone: str = "UTC",
    timezone_labels: TimezoneMap | None = None,
    db: Optional[AsyncSession] = None,
) -> dict[str, Any]:
    if not calendar_ids:
        calendar_ids = ["primary"]

    busy_periods: list[dict[str, datetime]] = []
    for window in search_windows:
        try:
            fb_result = await get_freebusy(
                user_id=user_id,
                calendar_ids=calendar_ids,
                time_min=window["start"],
                time_max=window["end"],
                db=db,
            )
            for cal_entry in fb_result.get("calendars", {}).values():
                for busy in cal_entry.get("busy", []):
                    busy_start = datetime.fromisoformat(busy["start"]).replace(tzinfo=timezone.utc) if isinstance(busy["start"], str) else busy["start"]
                    busy_end = datetime.fromisoformat(busy["end"]).replace(tzinfo=timezone.utc) if isinstance(busy["end"], str) else busy["end"]
                    busy_periods.append({"start": busy_start, "end": busy_end})
        except Exception as exc:
            logger.warning(f"Free/busy check failed for window {window}: {exc}")

    double_book_warnings: list[dict[str, Any]] = []
    if db is not None:
        try:
            result = await db.execute(
                select(Meeting).where(
                    Meeting.user_id == user_id,
                    Meeting.status == "previewed",
                )
            )
            pending_meetings = result.scalars().all()
            for pm in pending_meetings:
                for slot in (pm.proposed_slots or []):
                    candidate_start = datetime.fromisoformat(slot.get("start")).replace(tzinfo=timezone.utc) if isinstance(slot.get("start"), str) else slot.get("start")
                    candidate_end = datetime.fromisoformat(slot.get("end")).replace(tzinfo=timezone.utc) if isinstance(slot.get("end"), str) else slot.get("end")
                    if candidate_start and candidate_end:
                        for window in search_windows:
                            ws, we = window["start"], window["end"]
                            if candidate_start < we and candidate_end > ws:
                                double_book_warnings.append({
                                    "meeting_id": str(pm.id),
                                    "title": slot.get("title", ""),
                                    "proposed_start": candidate_start.isoformat() if hasattr(candidate_start, "isoformat") else str(candidate_start),
                                    "proposed_end": candidate_end.isoformat() if hasattr(candidate_end, "isoformat") else str(candidate_end),
                                })
                                break
        except Exception as exc:
            logger.warning(f"Double-booking check failed: {exc}")

    free_slots = _compute_free_slots(
        search_windows=search_windows,
        busy_periods=busy_periods,
        duration_minutes=duration_minutes,
    )

    if timezone_labels is None:
        timezone_labels = {user_timezone: user_timezone}

    slots_with_tz = _annotate_timezones(free_slots, timezone_labels)

    return {
        "free_slots": slots_with_tz,
        "busy_periods": [
            {
                "start": b["start"].isoformat() if hasattr(b["start"], "isoformat") else b["start"],
                "end": b["end"].isoformat() if hasattr(b["end"], "isoformat") else b["end"],
            }
            for b in busy_periods
        ],
        "double_booking_warnings": double_book_warnings,
    }


def _compute_free_slots(
    search_windows: list[dict[str, datetime]],
    busy_periods: list[dict[str, datetime]],
    duration_minutes: int = 60,
) -> list[dict[str, str]]:
    merged_busy = _merge_busy_periods(busy_periods)
    free_slots: list[dict[str, str]] = []

    for window in search_windows:
        ws = window["start"]
        we = window["end"]
        cursor = ws
        while cursor + timedelta(minutes=duration_minutes) <= we:
            slot_end = cursor + timedelta(minutes=duration_minutes)
            is_free = True
            for busy in merged_busy:
                if cursor < busy["end"] and slot_end > busy["start"]:
                    is_free = False
                    cursor = busy["end"]
                    break
            if is_free:
                free_slots.append({
                    "start": cursor.isoformat(),
                    "end": slot_end.isoformat(),
                    "duration_minutes": duration_minutes,
                })
                cursor += timedelta(minutes=duration_minutes)
            else:
                continue

    return _rank_slots(free_slots)


def _merge_busy_periods(periods: list[dict[str, datetime]]) -> list[dict[str, datetime]]:
    if not periods:
        return []
    sorted_b = sorted(periods, key=lambda p: p["start"])
    merged: list[dict[str, datetime]] = [sorted_b[0]]
    for b in sorted_b[1:]:
        last = merged[-1]
        if b["start"] <= last["end"]:
            last["end"] = max(last["end"], b["end"])
        else:
            merged.append(b)
    return merged


def _rank_slots(slots: list[dict[str, str]]) -> list[dict[str, str]]:
    now = datetime.now(timezone.utc)
    future_slots = [s for s in slots if datetime.fromisoformat(s["start"]).replace(tzinfo=timezone.utc) > now]
    future_slots.sort(key=lambda s: datetime.fromisoformat(s["start"]).replace(tzinfo=timezone.utc))
    return future_slots


def _annotate_timezones(
    slots: list[dict[str, str]],
    timezone_labels: TimezoneMap,
) -> list[dict[str, Any]]:
    annotated: list[dict[str, Any]] = []
    for slot in slots:
        start_dt = datetime.fromisoformat(slot["start"]).replace(tzinfo=timezone.utc)
        tz_display: dict[str, str] = {}
        for tz_name, label in timezone_labels.items():
            local_dt = _to_tz_aware(start_dt, tz_name)
            tz_display[label] = local_dt.strftime("%Y-%m-%d %H:%M %Z")
        annotated.append({
            "start": slot["start"],
            "end": slot["end"],
            "duration_minutes": slot["duration_minutes"],
            "timezone_display": tz_display,
        })
    return annotated


async def compute_free_slots(
    user_id: uuid.UUID,
    calendar_ids: list[str],
    search_windows: list[dict[str, datetime]],
    duration_minutes: int = 60,
    user_timezone: str = "UTC",
    db: Optional[AsyncSession] = None,
) -> list[dict[str, Any]]:
    result = await check_availability(
        user_id=user_id,
        calendar_ids=calendar_ids,
        search_windows=search_windows,
        duration_minutes=duration_minutes,
        user_timezone=user_timezone,
        db=db,
    )
    return result["free_slots"]
