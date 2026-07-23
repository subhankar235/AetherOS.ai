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
from agents.supervisor import supervisor_graph
from agents.reply_agent.drafter import DraftOutput

async def main():
    async with AsyncSessionLocal() as db:
        user_res = await db.execute(select(User).limit(1))
        user = user_res.scalar_one_or_none()
        if not user:
            user = User(id=uuid.uuid4(), email="dev-token-nathsubhankar57@gmail.com", full_name="Subhankar Nath")
            db.add(user)
            await db.commit()

        email = EmailMetadata(
            id=uuid.uuid4(),
            user_id=user.id,
            gmail_message_id="msg_gpt_work_99",
            sender="ChatGPT <noreply@email.openai.com>",
            subject="Introducing ChatGPT Work",
            summary="ChatGPT Work can gather context, create polished outputs.",
        )
        db.add(email)
        await db.commit()

        session_id = str(uuid.uuid4())

        # TURN 1: Search email
        print("\n=== TURN 1: Search emails ===")
        res1 = await supervisor_graph.run(
            user_id=str(user.id),
            session_id=session_id,
            raw_input="give me last 3 email recent",
            input_mode="text"
        )
        ctx1 = res1.get("conversation_context", {})
        print(f"Active email ID in context: {ctx1.get('active_email_id')}")

        # TURN 2: Draft reply for first one
        print("\n=== TURN 2: Draft reply for the first one ===")
        mock_msg = {
            "id": "msg_gpt_work_99",
            "payload": {
                "headers": [
                    {"name": "From", "value": "ChatGPT <noreply@email.openai.com>"},
                    {"name": "Subject", "value": "Introducing ChatGPT Work"}
                ]
            }
        }
        mock_llm_out = DraftOutput(
            body="Hi ChatGPT Team,\n\nThank you for the update on ChatGPT Work. We would like to learn more.",
            has_gaps=False,
            gap_notes=[]
        )

        with patch("agents.reply_agent.drafter.fetch_message", new_callable=AsyncMock, return_value=mock_msg), \
             patch("agents.reply_agent.drafter._find_matching_playbook", new_callable=AsyncMock, return_value=None), \
             patch("agents.reply_agent.drafter.ChatOpenAI") as mock_llm_cls:

            mock_llm_cls.return_value.with_structured_output.return_value.ainvoke = AsyncMock(return_value=mock_llm_out)

            res2 = await supervisor_graph.run(
                user_id=str(user.id),
                session_id=session_id,
                raw_input="now generate a draft for the first one and notify me",
                input_mode="text",
                conversation_context=ctx1
            )

            msg2 = res2.get("agent_response", {}).get("result", {}).get("message")
            draft_id2 = res2.get("agent_response", {}).get("result", {}).get("draft_id")
            print(f"Draft ID Returned: {draft_id2}")
            print(f"Response Message:\n{msg2}")

            # Verify Database Draft Persistence
            draft_in_db = await db.scalar(select(Draft).where(Draft.id == uuid.UUID(draft_id2)))
            print(f"Draft exists in DB: {draft_in_db is not None}")
            print(f"Draft Status in DB: {draft_in_db.status if draft_in_db else 'N/A'}")
            print(f"Draft Body in DB:\n{draft_in_db.current_body if draft_in_db else 'N/A'}")

            assert draft_in_db is not None
            assert draft_in_db.status == "drafting"

    print("\n🎉 SUCCESS! END-TO-END DRAFT CREATION AND DATABASE PERSISTENCE VERIFIED PERFECTLY!")

if __name__ == "__main__":
    asyncio.run(main())
