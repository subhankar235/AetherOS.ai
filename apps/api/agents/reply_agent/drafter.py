import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.exceptions import NotFoundError, ExternalServiceError
from integrations.gmail_client import fetch_message, get_thread
from models.draft import Draft
from models.email_metadata import EmailMetadata
from models.thread import Thread
from models.playbook import Playbook
from agents.supervisor.prompts import INJECTION_GUARDRAIL

logger = logging.getLogger("agents.reply_agent.drafter")


class DraftOutput(BaseModel):
    body: str = Field(description="The full draft reply body text")
    has_gaps: bool = Field(description="Whether the draft has gaps where it couldn't find needed information")
    gap_notes: list[str] = Field(description="List of specific gaps where information was missing")


DRAFT_SYSTEM_PROMPT = """You are an AI email reply assistant. Write a grounded reply draft based on:

1. The original email thread context and sender metadata
2. Knowledge base context (if provided) — use these verified facts; do NOT fabricate unverified details
3. A playbook template (if provided) — follow its structure and tone
4. The user's historical tone (if available)

Rules:
- Write in the user's voice and tone
- Be concise, clear, and professional
- STRICT GAP DETECTION: If the knowledge base or thread context does NOT contain a needed factual answer (e.g., exact refund window, current pricing, specific policy dates, or technical SLA terms), you MUST set `has_gaps` to true, list each missing detail in `gap_notes`, and insert explicit gap placeholders in brackets directly into the body text, for example:
  `[I don't have our current refund window — please confirm]`
  Never fabricate policies, pricing, or unverified claims.
- Do NOT include a subject line or "Subject:" prefix in `body` — just the reply body text
- Do NOT include generic placeholder salutations in angle brackets like [Your Name] — use appropriate closing
""" + INJECTION_GUARDRAIL


async def generate_draft(
    user_id: uuid.UUID,
    email_id: uuid.UUID,
    db: AsyncSession,
    instructions: Optional[str] = None,
    user_timezone: str = "UTC",
) -> Draft:
    email_result = await db.execute(
        select(EmailMetadata).where(
            EmailMetadata.id == email_id,
            EmailMetadata.user_id == user_id,
        )
    )
    email_meta = email_result.scalar_one_or_none()
    if not email_meta:
        raise NotFoundError(f"Email {email_id} not found for user {user_id}")

    gmail_message_id = email_meta.gmail_message_id
    raw_message = None
    if gmail_message_id:
        try:
            raw_message = await fetch_message(user_id, gmail_message_id, db)
        except Exception as fetch_exc:
            logger.warning(f"Live Gmail fetch failed for msg {gmail_message_id}, using stored metadata: {fetch_exc}")

    headers = {}
    if raw_message:
        payload = raw_message.get("payload", {})
        headers = {h["name"]: h["value"] for h in payload.get("headers", [])}
        body_text = _extract_body_text(payload)
        subject = headers.get("Subject", email_meta.subject or "(no subject)")
        sender = headers.get("From", email_meta.sender or "(unknown)")
    else:
        subject = email_meta.subject or "(no subject)"
        sender = email_meta.sender or "(unknown)"
        body_text = email_meta.summary or "Request for follow up and details."

    thread_content = ""
    if raw_message:
        gmail_thread_id = raw_message.get("threadId", "")
        if gmail_thread_id:
            try:
                thread_data = await get_thread(user_id, gmail_thread_id, db)
                messages = thread_data.get("messages", [])
                thread_content = _format_thread_summary(messages)
            except Exception as exc:
                logger.warning(f"Failed to fetch thread {gmail_thread_id}: {exc}")

    # Query Knowledge Agent (Phase 14) for factual context grounding using a derived query
    kb_context = ""
    try:
        from agents.knowledge_agent.retriever import query_knowledge
        derived_query = f"{subject} {body_text[:200]}"
        kb_res = await query_knowledge(
            query=derived_query,
            user_id=user_id,
            org_id="default_org",
            access_level="Member",
            db=db,
        )
        if kb_res and kb_res.get("result", {}).get("answer"):
            kb_context = kb_res["result"]["answer"]
    except Exception as kb_exc:
        logger.warning(f"Knowledge Agent query in drafter skipped: {kb_exc}")

    playbook = await _find_matching_playbook(db, email_meta, body_text)

    prompt_parts = [
        f"## Original Email Metadata & Content\nSubject: {subject}\nFrom: {sender}\nBody:\n{body_text[:3000]}\n",
    ]
    if thread_content:
        prompt_parts.append(f"## Thread Context (newest last)\n{thread_content[:4000]}\n")
    if kb_context:
        prompt_parts.append(f"## Knowledge Base Context (Factual Chunks)\n{kb_context[:2000]}\n")
    if playbook:
        prompt_parts.append(
            f"## Matching Playbook\nName: {playbook.name}\n"
            f"Type: {playbook.scenario_type}\n"
            f"Template: {playbook.template_structure}\n"
            f"Tone: {json.dumps(playbook.tone_settings)}\n"
        )
    if instructions:
        prompt_parts.append(f"## User Instructions\n{instructions}\n")

    user_prompt = "\n---\n".join(prompt_parts)

    from core.llm_factory import get_provider_candidates

    candidates = get_provider_candidates(is_classifier=False)
    if not candidates:
        candidates = [{
            "name": "openai",
            "model": getattr(settings, "OPENAI_MODEL_PRIMARY", "gpt-4o-mini"),
            "api_key": settings.OPENAI_API_KEY,
            "base_url": getattr(settings, "openai_base_url", None),
        }]

    result: Optional[DraftOutput] = None
    last_exc: Optional[Exception] = None

    for cand in candidates:
        try:
            logger.info(f"Attempting draft generation via LLM provider '{cand['name']}' using model '{cand['model']}'...")
            kwargs = {
                "model": cand["model"],
                "temperature": 0.3,
                "api_key": cand["api_key"],
            }
            if cand.get("base_url"):
                kwargs["base_url"] = cand["base_url"]

            llm = ChatOpenAI(**kwargs)
            try:
                structured_llm = llm.with_structured_output(DraftOutput)
                result = await structured_llm.ainvoke([
                    {"role": "system", "content": DRAFT_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ])
            except Exception as s_exc:
                logger.info(f"Structured output json_schema method failed for '{cand['name']}': {s_exc}. Retrying with JSON prompt fallback...")
                json_prompt = (
                    f"{user_prompt}\n\n"
                    f"IMPORTANT: You MUST respond strictly in valid JSON format with no extra markdown wrapping:\n"
                    f'{{"body": "reply draft body text", "has_gaps": false, "gap_notes": []}}'
                )
                raw_resp = await llm.ainvoke([
                    {"role": "system", "content": DRAFT_SYSTEM_PROMPT},
                    {"role": "user", "content": json_prompt},
                ])
                raw_content = getattr(raw_resp, "content", str(raw_resp)).strip()
                if "```json" in raw_content:
                    raw_content = raw_content.split("```json")[1].split("```")[0].strip()
                elif "```" in raw_content:
                    raw_content = raw_content.split("```")[1].split("```")[0].strip()

                parsed = json.loads(raw_content)
                result = DraftOutput(
                    body=parsed.get("body", raw_content),
                    has_gaps=bool(parsed.get("has_gaps", False)),
                    gap_notes=parsed.get("gap_notes", []),
                )

            if result and result.body:
                logger.info(f"Draft generation succeeded using provider '{cand['name']}'.")
                break
        except Exception as exc:
            last_exc = exc
            logger.warning(f"Draft generation attempt failed for provider '{cand['name']}': {exc}")

    if not result:
        logger.error(f"All LLM provider attempts failed for draft generation. Last error: {last_exc}")
        sender_clean = sender.split("<")[0].strip().replace('"', '') or "there"
        fallback_body = (
            f"Hi {sender_clean},\n\n"
            f"Thank you for your email regarding '{subject}'. I have received your message and will review the details to follow up with you shortly.\n\n"
            f"Best regards,"
        )
        result = DraftOutput(
            body=fallback_body,
            has_gaps=False,
            gap_notes=[],
        )

    draft_body = result.body
    if result.has_gaps and result.gap_notes:
        notes_formatted = "\n\n[Draft Notes — Gaps detected: " + "; ".join(result.gap_notes) + "]"
        if notes_formatted not in draft_body:
            draft_body = draft_body + notes_formatted

    local_thread_id = email_meta.thread_id

    version_entry = {
        "version": 1,
        "body": draft_body,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "ai_generated",
        "instructions": instructions,
        "has_gaps": result.has_gaps,
        "gap_notes": result.gap_notes,
    }

    draft = Draft(
        id=uuid.uuid4(),
        user_id=user_id,
        email_id=email_id,
        thread_id=local_thread_id,
        current_body=draft_body,
        version_history=[version_entry],
        status="drafting",
    )
    setattr(draft, "has_gaps", result.has_gaps)
    setattr(draft, "gap_notes", result.gap_notes)

    db.add(draft)
    await db.commit()
    await db.refresh(draft)

    # Persist session state to Redis if Redis available
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        redis_key = f"draft:{draft.id}"
        await r.hset(redis_key, mapping={
            "draft_id": str(draft.id),
            "user_id": str(user_id),
            "email_id": str(email_id),
            "status": "drafting",
            "current_body": draft_body,
            "has_gaps": "1" if result.has_gaps else "0",
            "gap_notes": json.dumps(result.gap_notes),
        })
        await r.expire(redis_key, 86400)  # 24h expiration
        await r.close()
    except Exception as red_exc:
        logger.warning(f"Redis session mirror skipped: {red_exc}")

    logger.info(
        f"Generated draft {draft.id} for email {email_id}, "
        f"has_gaps={result.has_gaps}, gaps={result.gap_notes}"
    )

    return draft


async def _find_matching_playbook(
    db: AsyncSession,
    email_meta: EmailMetadata,
    body_text: str,
) -> Optional[Playbook]:
    try:
        result = await db.execute(
            select(Playbook).where(
                Playbook.user_id == email_meta.user_id,
            )
        )
        playbooks = result.scalars().all()

        if not playbooks:
            return None

        combined = f"Subject: {email_meta.subject}\nBody: {body_text[:2000]}"

        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.0,
            api_key=settings.OPENAI_API_KEY,
        )

        playbook_list = "\n".join(
            f"- {p.name} (type: {p.scenario_type}): {p.template_structure[:100]}"
            for p in playbooks
        )

        response = await llm.ainvoke([
            {"role": "system", "content": "Select the best matching playbook for this email, or respond with 'none' if none match. Respond with only the playbook name."},
            {"role": "user", "content": f"Available playbooks:\n{playbook_list}\n\nEmail:\n{combined}\n\nBest playbook name or 'none':"},
        ])

        selected_name = (response.content if hasattr(response, "content") else str(response)).strip()
        for p in playbooks:
            if p.name.lower() == selected_name.lower():
                logger.info(f"Matched playbook '{p.name}' to email {email_meta.id}")
                return p

        return None

    except Exception as exc:
        logger.warning(f"Playbook matching failed: {exc}")
        return None


def _extract_body_text(payload: dict) -> str:
    import base64, re
    text_parts = []

    def _walk(part: dict):
        mime_type = part.get("mimeType", "")
        if mime_type == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                try:
                    decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                    text_parts.append(decoded)
                except Exception:
                    pass
        elif mime_type == "text/html":
            data = part.get("body", {}).get("data", "")
            if data:
                try:
                    decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                    clean = re.sub(r"<[^>]+>", " ", decoded)
                    clean = re.sub(r"\s+", " ", clean).strip()
                    text_parts.append(clean)
                except Exception:
                    pass
        for sub in part.get("parts", []):
            _walk(sub)

    _walk(payload)
    return "\n".join(text_parts)


def _format_thread_summary(messages: list[dict]) -> str:
    parts = []
    for idx, msg in enumerate(messages):
        payload = msg.get("payload", {})
        headers = {h["name"]: h["value"] for h in payload.get("headers", [])}
        body = _extract_body_text(payload)
        parts.append(
            f"[{idx + 1}] From: {headers.get('From', '?')} | "
            f"Date: {headers.get('Date', '?')}\n{body[:1000]}\n"
        )
    return "\n".join(parts[-10:])
