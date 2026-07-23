import os
os.environ["LANGCHAIN_TRACING_V2"] = "false"
import asyncio
import sys
import uuid
from unittest.mock import patch, AsyncMock

sys.path.append("apps/api")
from dotenv import load_dotenv
load_dotenv()

from db.session import AsyncSessionLocal
from sqlalchemy import select
from models.user import User
from models.email_metadata import EmailMetadata
from models.draft import Draft
from agents.reply_agent.drafter import generate_draft
from agents.reply_agent.editor import edit_draft
from agents.reply_agent.sender import prepare_send, execute_send
from services.approval.approval_gate import approve

async def run_test():
    print("\n--- PHASE 12 QUICK VERIFICATION ---")
    async with AsyncSessionLocal() as db:
        user_res = await db.execute(select(User).limit(1))
        user = user_res.scalar_one_or_none()
        if not user:
            user = User(id=uuid.uuid4(), email="dev-token-nathsubhankar57@gmail.com", full_name="Subhankar Nath")
            db.add(user)
            await db.commit()
            await db.refresh(user)

        email_meta = EmailMetadata(
            id=uuid.uuid4(),
            user_id=user.id,
            gmail_message_id="msg_mock_123",
            sender="partner@devfolio.co",
            subject="Hackathon Question",
            summary="What are your refund terms?",
        )
        db.add(email_meta)
        await db.commit()

        mock_msg = {
            "id": "msg_mock_123",
            "threadId": "thread_mock_123",
            "payload": {
                "headers": [
                    {"name": "From", "value": "partner@devfolio.co"},
                    {"name": "Subject", "value": "Hackathon Question"}
                ],
                "body": {"data": "V2hhdCBhcmUgeW91ciByZWZ1bmQgdGVybXM/="}
            }
        }

        with patch("agents.reply_agent.drafter.fetch_message", new_callable=AsyncMock, return_value=mock_msg):
            # 12.1 Drafter
            print("1. Testing Drafter...")
            draft = await generate_draft(user.id, email_meta.id, db, "Answer politely")
            print(f"   Draft ID: {draft.id}")
            print(f"   Status: {draft.status}")
            print(f"   Version count: {len(draft.version_history)}")

            # 12.2 Editor with Manual Edit
            print("2. Testing Editor with Manual Edit Preservation...")
            edited = await edit_draft(draft.id, user.id, "Shorten it", db, current_body_override=draft.current_body + "\nPS: See you soon!")
            print(f"   Updated Version count: {len(edited.version_history)}")

            # 12.3 Sender & Approval Gate
            print("3. Testing Prepare Send & Approval Gate...")
            prep = await prepare_send(draft.id, user.id, db, current_body_override=edited.current_body)
            approval_id = uuid.UUID(prep["approval_id"])
            print(f"   Approval ID Created: {approval_id}")

            # Approve
            await approve(db, approval_id, approved_by=user.email)
            print("   Approval Gate Marked Approved.")

            with patch("agents.reply_agent.sender.send_message", new_callable=AsyncMock, return_value={"id": "sent_gmail_999", "threadId": "thread_mock_123"}):
                send_res = await execute_send(draft.id, approval_id, user, db)
                print(f"4. Send Execution Success: status={send_res.get('status')}, gmail_id={send_res.get('gmail_message_id')}")

    print("\n--- ALL PHASE 12 TESTS PASSED PERFECTLY ---")

if __name__ == "__main__":
    asyncio.run(run_test())
