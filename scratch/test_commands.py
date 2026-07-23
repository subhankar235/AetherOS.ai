import os
os.environ["LANGCHAIN_TRACING_V2"] = "false"
import asyncio
import sys

sys.path.append("apps/api")
from dotenv import load_dotenv
load_dotenv()

from agents.supervisor.intent_router import classify_intent

async def main():
    commands = [
        "draft a polite email response to standard terms",
        "schedule a meeting tomorrow at 3pm with Bob",
        "what is our company refund policy?"
    ]
    for cmd in commands:
        print(f"\n==========================================")
        print(f"COMMAND: '{cmd}'")
        res = await classify_intent(cmd, {})
        print(f"INTENT: {res.get('intent')}")
        print(f"TASKS: {res.get('tasks')}")
        print(f"CLARIFICATION: {res.get('clarification_text')}")
        print(f"==========================================")

if __name__ == "__main__":
    asyncio.run(main())
