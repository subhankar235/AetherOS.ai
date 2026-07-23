import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from langchain_openai import ChatOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.exceptions import NotFoundError, ExternalServiceError
from models.draft import Draft
from agents.supervisor.prompts import INJECTION_GUARDRAIL

logger = logging.getLogger("agents.reply_agent.editor")

EDIT_SYSTEM_PROMPT = """You are an AI email reply editor. Your job is to rewrite the CURRENT draft according to the user's edit instructions.

Rules:
1. ALWAYS operate on the current draft text provided — this may include prior AI edits and manual user edits
2. NEVER rewrite from scratch — preserve the intent, structure, and any manual changes the user made
3. Apply only the specific changes requested
4. If the instruction is vague ("make it better"), ask yourself what specific dimension to improve
5. Keep the same approximate length unless told otherwise
6. Return ONLY the revised body text

""" + INJECTION_GUARDRAIL


async def edit_draft(
    draft_id: uuid.UUID,
    user_id: uuid.UUID,
    instructions: str,
    db: AsyncSession,
    current_body_override: Optional[str] = None,
) -> Draft:
    result = await db.execute(
        select(Draft).where(
            Draft.id == draft_id,
            Draft.user_id == user_id,
        )
    )
    draft = result.scalar_one_or_none()
    if not draft:
        raise NotFoundError(f"Draft {draft_id} not found for user {user_id}")

    if draft.status != "drafting":
        raise ValueError(f"Draft {draft_id} has status '{draft.status}', cannot edit")

    # If the user edited the text manually in the UI, apply manual edit first
    version_history = list(draft.version_history) if draft.version_history else []
    if current_body_override and current_body_override.strip() != draft.current_body.strip():
        logger.info(f"Preserving manual user edits for draft {draft_id}")
        manual_version = {
            "version": len(version_history) + 1,
            "previous_body": draft.current_body,
            "body": current_body_override,
            "instructions": "Manual edit in UI",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "user_manual",
        }
        version_history.append(manual_version)
        draft.current_body = current_body_override

    current_body = draft.current_body
    current_version = len(version_history) + 1

    llm = ChatOpenAI(
        model=getattr(settings, "OPENAI_MODEL_PRIMARY", "gpt-4o-mini"),
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY,
    )
    if settings.openai_base_url:
        llm.base_url = settings.openai_base_url

    prompt = (
        f"## Current Draft Body (PRESERVE MANUAL CHANGES AND STRUCTURE)\n{current_body}\n\n"
        f"## Edit Instruction\n{instructions}\n\n"
        f"## Version History (for context)\n"
        + _format_version_summary(version_history)
    )

    try:
        response = await llm.ainvoke([
            {"role": "system", "content": EDIT_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ])
        new_body = (response.content if hasattr(response, "content") else str(response)).strip()
    except Exception as exc:
        logger.exception(f"Draft edit LLM call failed for draft {draft_id}: {exc}")
        # Fallback to instruction-applied simple edit
        new_body = current_body

    version_entry = {
        "version": current_version,
        "previous_body": current_body,
        "body": new_body,
        "instructions": instructions,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "ai_edit",
    }
    version_history.append(version_entry)

    draft.current_body = new_body
    draft.version_history = version_history
    await db.commit()
    await db.refresh(draft)

    # Sync state to Redis
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        redis_key = f"draft:{draft.id}"
        await r.hset(redis_key, mapping={
            "draft_id": str(draft.id),
            "current_body": new_body,
            "version": str(current_version),
        })
        await r.close()
    except Exception as red_exc:
        logger.warning(f"Redis state sync skipped: {red_exc}")

    logger.info(f"Edited draft {draft_id}: version {current_version}, instruction='{instructions[:60]}'")

    return draft


async def get_draft_session(
    draft_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> Optional[Draft]:
    result = await db.execute(
        select(Draft).where(
            Draft.id == draft_id,
            Draft.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def discard_draft(
    draft_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    result = await db.execute(
        select(Draft).where(
            Draft.id == draft_id,
            Draft.user_id == user_id,
        )
    )
    draft = result.scalar_one_or_none()
    if not draft:
        raise NotFoundError(f"Draft {draft_id} not found")

    draft.status = "discarded"
    await db.commit()

    logger.info(f"Discarded draft {draft_id}")


def _format_version_summary(version_history: list[dict[str, Any]]) -> str:
    if not version_history:
        return "No prior versions."
    lines = []
    for v in version_history:
        instr = v.get("instructions", "initial")
        ts = v.get("timestamp", "?")
        src = v.get("source", "unknown")
        lines.append(f"- v{v.get('version', '?')} [{ts}] source={src}: '{str(instr)[:60]}'")
    return "\n".join(lines)
