import asyncio
import json
import uuid
import sys
from datetime import datetime, timezone

sys.path.insert(0, ".")

from db.session import AsyncSessionLocal
from models.user import User, UserRole
from models.email_metadata import EmailMetadata
from agents.supervisor.graph import SupervisorGraph

async def main():
    print("Testing Supervisor Graph AI Reply Agent backend execution with user email context...")
    
    async with AsyncSessionLocal() as db:
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            clerk_user_id=f"clerk_{uuid.uuid4().hex[:8]}",
            email=f"testuser_{uuid.uuid4().hex[:4]}@example.com",
            role=UserRole.MEMBER,
        )
        db.add(user)
        await db.commit()  # Commit user first so foreign key is satisfied in DB
        
        email_meta = EmailMetadata(
            id=uuid.uuid4(),
            user_id=user_id,
            gmail_message_id=f"msg_{uuid.uuid4().hex[:8]}",
            sender="Devfolio Team <team@devfolio.co>",
            subject="Inquiry regarding partnership and subscription terms",
            summary="Hi, I would like to confirm our partnership details and subscription terms.",
            priority="High",
            category="General",
            received_at=datetime.now(timezone.utc),
        )
        db.add(email_meta)
        await db.commit()

    sg = SupervisorGraph()
    res = await sg.run(
        user_id=str(user_id),
        session_id="session_test_123",
        raw_input="draft reply to Devfolio inquiry regarding partnership details",
        input_mode="text"
    )
    
    print("\n================ BACKEND AI RESPONSE ================")
    print(json.dumps(res, indent=2, default=str))
    print("=====================================================")

if __name__ == "__main__":
    asyncio.run(main())
