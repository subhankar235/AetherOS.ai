import os
os.environ["LANGCHAIN_TRACING_V2"] = "false"
import asyncio
import sys
import uuid

sys.path.append("apps/api")
from dotenv import load_dotenv
load_dotenv()

from db.session import AsyncSessionLocal
from sqlalchemy import select
from models.user import User
from models.email_metadata import EmailMetadata
from models.draft import Draft
from agents.supervisor.graph import run_reply_agent

async def main():
    async with AsyncSessionLocal() as db:
        user_res = await db.execute(select(User).limit(1))
        user = user_res.scalar_one_or_none()
        if not user:
            user = User(id=uuid.uuid4(), email="dev-token-nathsubhankar57@gmail.com", full_name="Subhankar Nath")
            db.add(user)
            await db.commit()

        print(f"User ID: {user.id}")

        # 1. Run supervisor reply agent to generate draft
        res = await run_reply_agent("draft", {"_user_id": str(user.id), "instructions": "reply regarding partnership"})
        draft_id_str = res["result"]["draft_id"]
        print(f"1. Supervisor Generated Draft ID: {draft_id_str}")

        # 2. Query DB to verify Draft exists with status drafting
        draft_db = await db.scalar(select(Draft).where(Draft.id == uuid.UUID(draft_id_str)))
        assert draft_db is not None
        assert draft_db.status == "drafting"
        print(f"2. DB Draft status: {draft_db.status}")

        # 3. Query all drafting status items for user (same query router GET /replies/drafts does)
        drafts_res = await db.execute(select(Draft).where(Draft.user_id == user.id, Draft.status == "drafting"))
        active_drafts = drafts_res.scalars().all()
        print(f"3. Active Drafts Count for User: {len(active_drafts)}")

    print("\n✅ REAL END-TO-END FLOW VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(main())
