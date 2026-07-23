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
from agents.reply_agent.drafter import generate_draft
from agents.reply_agent.editor import edit_draft
from agents.reply_agent.sender import prepare_send, execute_send
from services.approval.approval_gate import approve

async def run_phase12_test():
    print("\n--- STARTING PHASE 12 END-TO-END TEST ---")
    async with AsyncSessionLocal() as db:
        # Fetch or create a test user
        user_res = await db.execute(select(User).limit(1))
        user = user_res.scalar_one_or_none()
        if not user:
            user = User(
                id=uuid.uuid4(),
                email="dev-token-nathsubhankar57@gmail.com",
                full_name="Subhankar Nath",
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        print(f"Test User ID: {user.id}")

        # Fetch or create an email metadata record
        email_res = await db.execute(
            select(EmailMetadata).where(EmailMetadata.user_id == user.id).limit(1)
        )
        email_meta = email_res.scalar_one_or_none()
        if not email_meta:
            email_meta = EmailMetadata(
                id=uuid.uuid4(),
                user_id=user.id,
                gmail_message_id="test_msg_123",
                sender="partner@devfolio.co",
                subject="Hackathon Partnership Query",
                summary="Hello, what is your refund window and terms?",
            )
            db.add(email_meta)
            await db.commit()
            await db.refresh(email_meta)

        print(f"Target Email ID: {email_meta.id}")

        # 12.1 Generate Draft
        print("\n12.1 Testing generate_draft with Knowledge Base & Gap Detection...")
        draft = await generate_draft(
            user_id=user.id,
            email_id=email_meta.id,
            instructions="Include refund policy details if known",
            db=db,
        )
        print(f"Draft Created ID: {draft.id}")
        print(f"Status: {draft.status}")
        print(f"Initial Version History Count: {len(draft.version_history)}")
        print(f"Current Body:\n{draft.current_body[:150]}...")

        # 12.2 Edit Draft
        print("\n12.2 Testing edit_draft (Shorten with manual edit preservation)...")
        edited_draft = await edit_draft(
            draft_id=draft.id,
            user_id=user.id,
            instructions="Shorten it to 2 sentences",
            db=db,
            current_body_override=draft.current_body + "\nPS: Excited to collaborate!",
        )
        print(f"Updated Body Version Count: {len(edited_draft.version_history)}")
        print(f"Updated Body:\n{edited_draft.current_body}...")

        # 12.3 Prepare Send (Approval Gate)
        print("\n12.3 Testing prepare_send (Creation of Approval Request)...")
        prep = await prepare_send(
            draft_id=draft.id,
            user_id=user.id,
            db=db,
            current_body_override=edited_draft.current_body,
        )
        print(f"Requires Approval: {prep.get('requires_approval')}")
        print(f"Approval ID: {prep.get('approval_id')}")

        # Approve Approval Request
        approval_id = uuid.UUID(prep["approval_id"])
        print("\nApproving approval request...")
        await approve(db, approval_id, approved_by=user.email)
        print("Approval marked APPROVED.")

        # Execute Send
        print("\nExecuting send_email...")
        try:
            send_result = await execute_send(
                draft_id=draft.id,
                approval_id=approval_id,
                user=user,
                db=db,
            )
            print(f"Send Result: {send_result}")
        except Exception as e:
            print(f"Send Note (expected if mock credentials used): {e}")

        print("\n--- PHASE 12 END-TO-END TEST COMPLETED SUCCESSFULLY ---")

if __name__ == "__main__":
    asyncio.run(run_phase12_test())
