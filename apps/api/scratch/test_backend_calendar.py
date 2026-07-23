import asyncio
import json
import uuid
import sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, ".")

from db.session import AsyncSessionLocal
from models.user import User, UserRole
from models.meeting import Meeting
from agents.supervisor.graph import SupervisorGraph

async def main():
    print("Testing Supervisor Graph Calendar Agent backend execution...")
    
    async with AsyncSessionLocal() as db:
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            clerk_user_id=f"clerk_{uuid.uuid4().hex[:8]}",
            email=f"testuser_{uuid.uuid4().hex[:4]}@example.com",
            role=UserRole.MEMBER,
        )
        db.add(user)
        await db.commit()

        # Seed an existing pending meeting proposal to trigger double-booking warning
        now = datetime.now(timezone.utc)
        pending = Meeting(
            id=uuid.uuid4(),
            user_id=user_id,
            proposed_slots=[{
                "start": (now + timedelta(days=1)).replace(hour=14, minute=0, second=0).isoformat(),
                "end": (now + timedelta(days=1)).replace(hour=15, minute=0, second=0).isoformat(),
                "title": "Existing Overlapping Proposal"
            }],
            participants=[{"email": "team@example.com"}],
            status="previewed",
        )
        db.add(pending)
        await db.commit()

    sg = SupervisorGraph()
    res = await sg.run(
        user_id=str(user_id),
        session_id="session_calendar_test",
        raw_input="schedule a 60 min project review meeting with team@example.com for tomorrow afternoon",
        input_mode="text"
    )
    
    print("\n================ BACKEND CALENDAR AI RESPONSE ================")
    print(json.dumps(res, indent=2, default=str))
    print("==============================================================")

    result_data = res["result"]
    assert "preview_id" in result_data, "Missing preview_id"
    assert "approval_id" in result_data, "Missing approval_id"
    assert "meet_link" in result_data, "Missing meet_link"
    assert "double_booking_warnings" in result_data, "Missing double_booking_warnings"
    assert len(result_data["double_booking_warnings"]) > 0, "Double-booking warning not triggered!"
    print("\nSUCCESS: Calendar Agent returned complete payload with Google Meet link & double-booking warning!")

if __name__ == "__main__":
    asyncio.run(main())
