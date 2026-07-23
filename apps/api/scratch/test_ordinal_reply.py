import asyncio
import json
import uuid
import sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, ".")

from db.session import AsyncSessionLocal
from models.user import User, UserRole
from models.email_metadata import EmailMetadata
from agents.supervisor.graph import SupervisorGraph

async def main():
    print("Testing Ordinal Context Resolution ('write a draft for the first email')...")
    
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
        
        now = datetime.now(timezone.utc)
        
        # Email 1: Quora Digest (First email - most recent)
        email1 = EmailMetadata(
            id=uuid.uuid4(),
            user_id=user_id,
            gmail_message_id=f"msg_{uuid.uuid4().hex[:8]}",
            sender="Quora Digest <english-quora-digest@quora.com>",
            subject="My daughter wants a cucumber. What should I do?",
            summary="Give her the cucumber. Wash it first. Hand it over. That is it.",
            priority="Medium",
            category="General",
            received_at=now,
        )
        
        # Email 2: MLH (Second email - older)
        email2 = EmailMetadata(
            id=uuid.uuid4(),
            user_id=user_id,
            gmail_message_id=f"msg_{uuid.uuid4().hex[:8]}",
            sender="Major League Hacking <hi@mlh.io>",
            subject="Everything you'll need to know from MLH at Hexafalls 2",
            summary="We can't wait to see you this weekend at Hexafalls 2!",
            priority="High",
            category="General",
            received_at=now - timedelta(minutes=10),
        )
        
        db.add_all([email1, email2])
        await db.commit()

    sg = SupervisorGraph()
    
    # 1. First run search command to populate last_search_results in context
    search_res = await sg.run(
        user_id=str(user_id),
        session_id="session_test_ordinal",
        raw_input="find my recent emails",
        input_mode="text"
    )
    print("Search Result items count:", search_res["result"]["results_count"])
    print("Item 1 (first):", search_res["result"]["items"][0]["subject"])
    print("Item 2 (second):", search_res["result"]["items"][1]["subject"])
    
    # 2. Next run reply command asking for 'first email'
    draft_res = await sg.run(
        user_id=str(user_id),
        session_id="session_test_ordinal",
        raw_input="write a draft for the first email",
        input_mode="text"
    )
    
    print("\n================ BACKEND AI DRAFT RESPONSE ================")
    print("Target Email Subject:", draft_res["result"]["target_email"]["subject"])
    print("Target Email Sender:", draft_res["result"]["target_email"]["sender"])
    print("Draft Body Preview:\n", draft_res["result"]["draft_body"][:200])
    print("===========================================================")

    assert "cucumber" in draft_res["result"]["target_email"]["subject"].lower() or "quora" in draft_res["result"]["target_email"]["sender"].lower(), "FAILED: Did not target the first email!"
    print("\nSUCCESS: Correctly resolved 'first email' to Quora Digest / Cucumber email!")

if __name__ == "__main__":
    asyncio.run(main())
