import os
os.environ["LANGCHAIN_TRACING_V2"] = "false"
import asyncio
import sys
import uuid
from unittest.mock import patch, AsyncMock, MagicMock

sys.path.append("apps/api")
from dotenv import load_dotenv
load_dotenv()

from db.session import AsyncSessionLocal
from sqlalchemy import select
from models.user import User
from models.email_metadata import EmailMetadata
from agents.reply_agent.drafter import generate_draft, DraftOutput
from agents.reply_agent.editor import edit_draft
from agents.reply_agent.sender import prepare_send, execute_send
from services.approval.approval_gate import approve

async def main():
    async with AsyncSessionLocal() as db:
        user_res = await db.execute(select(User).limit(1))
        user = user_res.scalar_one_or_none()
        if not user:
            user = User(id=uuid.uuid4(), email="dev-token-nathsubhankar57@gmail.com", full_name="Subhankar Nath")
            db.add(user)
            await db.commit()

        email_meta = EmailMetadata(
            id=uuid.uuid4(),
            user_id=user.id,
            gmail_message_id="msg_fast_1",
            sender="partner@devfolio.co",
            subject="Hackathon Inquiry",
            summary="What is the refund policy?",
        )
        db.add(email_meta)
        await db.commit()

        mock_msg = {
            "id": "msg_fast_1",
            "payload": {
                "headers": [
                    {"name": "From", "value": "partner@devfolio.co"},
                    {"name": "Subject", "value": "Hackathon Inquiry"}
                ]
            }
        }

        mock_llm_out = DraftOutput(
            body="Hi Partner,\n\nThanks for reaching out! Here are the details.",
            has_gaps=False,
            gap_notes=[]
        )

        with patch("agents.reply_agent.drafter.fetch_message", new_callable=AsyncMock, return_value=mock_msg), \
             patch("agents.reply_agent.drafter._find_matching_playbook", new_callable=AsyncMock, return_value=None), \
             patch("agents.reply_agent.drafter.ChatOpenAI") as mock_llm_cls, \
             patch("agents.reply_agent.editor.ChatOpenAI") as mock_edit_cls:

            mock_llm_cls.return_value.with_structured_output.return_value.ainvoke = AsyncMock(return_value=mock_llm_out)
            mock_edit_cls.return_value.ainvoke = AsyncMock(return_value=MagicMock(content="Hi Partner,\n\nShortened version."))

            # 1. Draft
            draft = await generate_draft(user.id, email_meta.id, db, "be polite")
            print(f"1. DRAFTER CREATED DRAFT ID: {draft.id}")
            assert draft.status == "drafting"

            # 2. Edit with Manual Edit Preservation
            edited = await edit_draft(
                draft.id,
                user.id,
                "shorten it",
                db,
                current_body_override=draft.current_body + "\nPS: Manual edit added"
            )
            print(f"2. EDITED DRAFT VERSION COUNT: {len(edited.version_history)}")
            assert len(edited.version_history) >= 2

            # 3. Prepare Send
            prep = await prepare_send(draft.id, user.id, db, current_body_override=edited.current_body)
            appr_id = uuid.UUID(prep["approval_id"])
            print(f"3. APPROVAL REQUEST CREATED: {appr_id}")
            assert prep["requires_approval"] is True

            # 4. Approve
            await approve(db, appr_id, approved_by=user.email)
            print("4. APPROVAL GATE APPROVED")

            # 5. Execute Send
            with patch("agents.reply_agent.sender.send_message", new_callable=AsyncMock, return_value={"id": "sent_123", "threadId": "t_123"}):
                res = await execute_send(draft.id, appr_id, user, db)
                print(f"5. EXECUTE SEND RESULT: {res}")
                assert res["status"] == "sent"

    print("\n✅ ALL PHASE 12 TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    asyncio.run(main())
