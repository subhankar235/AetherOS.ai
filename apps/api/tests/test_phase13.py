import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from main import app
from core.deps import get_current_user
from agents.calendar_agent.extractor import extract_meeting_details, MeetingDetails, build_search_windows
from agents.calendar_agent.availability import check_availability, _compute_free_slots, _annotate_timezones
from agents.calendar_agent.event_creator import preview_event, confirm_event, request_approval_for_event
from models.user import User
from models.meeting import Meeting
from services.approval.approval_gate import create_approval_request, require_valid_approval

client = TestClient(app)

mock_user_id = uuid.uuid4()
mock_user = User(
    id=mock_user_id,
    clerk_user_id="user_clerk_phase13",
    email="testuser@example.com",
    name="Test User",
)


def override_get_current_user():
    return mock_user


app.dependency_overrides[get_current_user] = override_get_current_user


@pytest.mark.asyncio
async def test_extractor_entity_extraction():
    mock_llm = MagicMock()
    mock_structured = AsyncMock()
    mock_structured.ainvoke.return_value = MeetingDetails(
        title="Sync on AI Architecture",
        date="2026-07-25",
        time="14:00",
        duration_minutes=45,
        participants=["alex@example.com", "sarah@company.com"],
        description="Discuss agent boundaries",
        source_is_ambiguous=False,
    )
    mock_llm.with_structured_output.return_value = mock_structured

    res = await extract_meeting_details("Schedule a 45 min sync with alex@example.com and sarah@company.com on July 25 at 2pm", llm=mock_llm)
    assert res.title == "Sync on AI Architecture"
    assert res.duration_minutes == 45
    assert "alex@example.com" in res.participants


@pytest.mark.asyncio
async def test_availability_and_ranked_slots():
    windows = build_search_windows(preferred_date="2026-08-01", preferred_time="10:00", timezone_str="UTC")
    assert len(windows) > 0

    with patch("agents.calendar_agent.availability.get_freebusy") as mock_fb:
        mock_fb.return_value = {
            "calendars": {
                "primary": {
                    "busy": [
                        {"start": "2026-08-01T10:00:00Z", "end": "2026-08-01T11:00:00Z"}
                    ]
                }
            }
        }

        res = await check_availability(
            user_id=mock_user_id,
            calendar_ids=["primary"],
            search_windows=windows,
            duration_minutes=60,
            user_timezone="America/New_York",
            timezone_labels={"America/New_York": "Organizer (NY)", "UTC": "UTC"},
        )

        assert "free_slots" in res
        assert "busy_periods" in res
        for slot in res["free_slots"]:
            assert "timezone_display" in slot
            assert "Organizer (NY)" in slot["timezone_display"]


@pytest.mark.asyncio
async def test_double_booking_warning_for_pending_proposal():
    mock_db = AsyncMock()
    pending_meeting = Meeting(
        id=uuid.uuid4(),
        user_id=mock_user_id,
        proposed_slots=[{
            "start": "2026-08-01T10:00:00+00:00",
            "end": "2026-08-01T11:00:00+00:00",
            "title": "Pending Proposal"
        }],
        status="previewed",
    )
    mock_scalar = MagicMock()
    mock_scalar.scalars.return_value.all.return_value = [pending_meeting]
    mock_db.execute.return_value = mock_scalar

    windows = [{
        "start": datetime(2026, 8, 1, 9, 0, tzinfo=timezone.utc),
        "end": datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc),
    }]

    with patch("agents.calendar_agent.availability.get_freebusy", return_value={"calendars": {}}):
        res = await check_availability(
            user_id=mock_user_id,
            calendar_ids=["primary"],
            search_windows=windows,
            duration_minutes=60,
            db=mock_db,
        )

        assert len(res["double_booking_warnings"]) == 1
        assert res["double_booking_warnings"][0]["meeting_id"] == str(pending_meeting.id)


@pytest.mark.asyncio
async def test_event_creator_preview_and_approval():
    mock_db = AsyncMock()
    details = MeetingDetails(
        title="Product Roadmap Review",
        duration_minutes=30,
        participants=["pm@example.com"],
        description="Quarterly review",
    )

    with patch("agents.calendar_agent.event_creator.log_agent_action", return_value=uuid.uuid4()):
        preview = await preview_event(
            db=mock_db,
            user_id=mock_user_id,
            meeting=details,
            slot_start="2026-08-01T14:00:00Z",
            slot_end="2026-08-01T14:30:00Z",
            generate_meet=True,
        )

        assert preview["title"] == "Product Roadmap Review"
        assert preview["conference_data"] is not None
        assert preview["requires_approval"] is True

        with patch("agents.calendar_agent.event_creator.create_approval_request", return_value=uuid.uuid4()) as mock_app_req:
            approval_id = await request_approval_for_event(mock_db, mock_user_id, preview)
            assert approval_id is not None
            mock_app_req.assert_called_once()


@pytest.mark.asyncio
async def test_event_creator_confirm():
    mock_db = AsyncMock()
    approval_id = uuid.uuid4()
    preview_id = str(uuid.uuid4())
    event_body = {
        "summary": "Confirmed Sync",
        "start": {"dateTime": "2026-08-01T14:00:00Z"},
        "end": {"dateTime": "2026-08-01T14:30:00Z"},
        "conferenceData": {"createRequest": {"requestId": "meet-123"}},
    }

    with patch("agents.calendar_agent.event_creator.require_valid_approval", return_value=True), \
         patch("agents.calendar_agent.event_creator.calendar_create_event") as mock_create_event, \
         patch("agents.calendar_agent.event_creator.log_agent_action"):

        mock_create_event.return_value = {
            "id": "cal_evt_999",
            "htmlLink": "https://calendar.google.com/event?id=cal_evt_999",
            "hangoutLink": "https://meet.google.com/abc-defg-hij",
        }

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await confirm_event(
            db=mock_db,
            user_id=mock_user_id,
            preview_id=preview_id,
            approval_id=approval_id,
            event_body=event_body,
        )

        assert result["status"] == "confirmed"
        assert result["calendar_event_id"] == "cal_evt_999"
        assert "https://meet.google.com/abc-defg-hij" in result["hangout_link"]


def test_calendar_api_routes():
    with patch("routers.calendar.extract_meeting_details") as mock_extract:
        mock_extract.return_value = MeetingDetails(
            title="Design Review",
            participants=["designer@example.com"],
        )
        res = client.post("/calendar/extract", json={"text": "Schedule design review with designer@example.com"})
        assert res.status_code == 200
        assert res.json()["title"] == "Design Review"
