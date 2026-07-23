import asyncio
import json
import uuid
import sys

sys.path.insert(0, ".")

from db.session import AsyncSessionLocal
from models.user import User, UserRole
from agents.supervisor.graph import SupervisorGraph

async def main():
    print("Testing query: 'give me email containing meeting link'")
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

    sg = SupervisorGraph()
    res = await sg.run(
        user_id=str(user_id),
        session_id="debug_session_1",
        raw_input="give me email containing meeting link",
        input_mode="text"
    )
    print("\n================ DEBUG QUERY RESPONSE ================")
    print(json.dumps(res, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())
