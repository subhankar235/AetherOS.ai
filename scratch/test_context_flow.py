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
            gmail_message_id="m_123",
            sender="ChatGPT <noreply@email.openai.com>",
            subject="Introducing ChatGPT Work",
            summary="ChatGPT Work can gather context."
        )
        db.add(email)
        await db.commit()

        session_id = str(uuid.uuid4())

        # TURN 1: Search email
        print("\n--- TURN 1 ---")
        res1 = await supervisor_graph.run(
            user_id=str(user.id),
            session_id=session_id,
            raw_input="give me last one email",
            input_mode="text"
        )
        context1 = res1.get("conversation_context", {})
        print(f"Turn 1 active_email_id: {context1.get('active_email_id')}")
        assert context1.get("active_email_id") is not None

        # TURN 2: Draft reply referencing this
        print("\n--- TURN 2 ---")
        mock_msg = {
            "id": "m_123",
            "payload": {
                "headers": [
                    {"name": "From", "value": "noreply@email.openai.com"},
                    {"name": "Subject", "value": "Introducing ChatGPT Work"}
                ]
            }
        }
        mock_llm_out = DraftOutput(
            body="Hi ChatGPT Team,\n\nThank you for the update on ChatGPT Work.",
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
                raw_input="now make draft for this and notify me",
                input_mode="text",
                conversation_context=context1
            )
            
            agent_msg = res2.get("agent_response", {}).get("result", {}).get("message")
            intent = res2.get("classification", {}).get("intent")
            print(f"Turn 2 Intent: {intent}")
            print(f"Turn 2 Response Message:\n{agent_msg}")

            assert intent != "clarification"
            assert "Generated New Reply Draft" in agent_msg

    print("\n✅ MULTI-TURN CONTEXT REFERENCE RESOLUTION PASSED PERFECTLY!")

if __name__ == "__main__":
    asyncio.run(main())
