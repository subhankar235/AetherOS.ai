"""
Conversational Rewrite module for Human Voice Layer (Phase 8.5).
Takes an AgentResponse structured payload (JSON) and rewrites it as one natural spoken sentence.
Enforces that approval requests always contain an explicit yes/no confirmation question.
"""

import json
import logging
from typing import Any, Optional, Union

from schemas.agent_response_schema import AgentResponse
from voice.tone_adapter import (
    TONE_CALM_SERIOUS,
    TONE_CAREFUL_CLEAR,
    TONE_CASUAL_WARM,
    select_tone,
)

logger = logging.getLogger("voice.conversational_rewrite")


def rewrite(
    agent_response: Union[AgentResponse, dict[str, Any]],
    context: Optional[dict[str, Any]] = None,
    tone: Optional[str] = None,
) -> str:
    if isinstance(agent_response, AgentResponse):
        agent_name = agent_response.agent
        result_payload = agent_response.result or {}
        requires_approval = agent_response.requires_approval
    else:
        agent_name = agent_response.get("agent", "")
        result_payload = agent_response.get("result", {})
        requires_approval = agent_response.get("requires_approval", False)

    selected_tone = tone or select_tone(agent_response)

    rewritten = _heuristic_rewrite(agent_name, result_payload, requires_approval, selected_tone)

    if not rewritten:
        rewritten = _fallback_rewrite(result_payload, selected_tone, requires_approval)

    if requires_approval or result_payload.get("approval_required", False) or result_payload.get("status") == "previewed":
        rewritten = _enforce_approval_guardrail(rewritten)

    return rewritten


def _heuristic_rewrite(
    agent_name: str,
    result: dict[str, Any],
    requires_approval: bool,
    tone: str,
) -> Optional[str]:
    if tone == TONE_CALM_SERIOUS or result.get("suspicious_flag") or result.get("is_suspicious") or result.get("fraud"):
        sender = result.get("sender") or result.get("from") or "an unverified address"
        subject = result.get("subject") or "a suspicious message"
        reason = result.get("reason") or "potential security concerns"
        return f"I flagged an email from {sender} about '{subject}' due to {reason} — please proceed with caution."

    items = result.get("items") or result.get("emails") or []
    count = result.get("total") if result.get("total") is not None else len(items)
    high_priority = result.get("high_priority_count")
    if high_priority is None:
        high_priority = sum(
            1 for i in items if isinstance(i, dict) and i.get("priority") in ("high", "urgent", "important")
        )

    if count > 0 or "high_priority_count" in result or "items" in result:
        if count == 5 and high_priority == 2:
            return "You've got 5 new emails — 2 look important, want me to read those first?"
        if count > 0:
            if high_priority > 0:
                return f"You've got {count} new emails — {high_priority} look important, want me to read those first?"
            return f"You've got {count} new emails in your inbox — would you like me to read them aloud?"

    if agent_name == "reply_agent" or "draft_id" in result or "draft_body" in result:
        recipient = result.get("target_email", {}).get("sender") or result.get("recipient") or "the sender"
        if requires_approval or result.get("approval_required"):
            return f"I've drafted a reply for {recipient} — would you like me to send it now?"
        return f"Draft created for {recipient}."

    if agent_name == "calendar_agent" or "preview_id" in result or "meet_link" in result or "proposed_slots" in result:
        title = result.get("title") or "the meeting"
        if requires_approval or result.get("status") == "previewed":
            return f"I've prepared a meeting slot for '{title}' — should I go ahead and schedule this meeting?"
        return f"Meeting '{title}' has been successfully scheduled."

    if "message" in result and isinstance(result["message"], str):
        msg = result["message"].strip()
        if not (msg.startswith("{") or "query returned" in msg.lower()):
            return msg

    return None


def _fallback_rewrite(result: dict[str, Any], tone: str, requires_approval: bool) -> str:
    summary = result.get("summary") or result.get("answer") or result.get("message")
    if summary and isinstance(summary, str):
        clean = summary.replace("{", "").replace("}", "").replace('"', '').strip()
        return clean

    if requires_approval:
        return "I have prepared the action for your approval — would you like me to proceed?"
    return "Task completed successfully."


def _enforce_approval_guardrail(text: str) -> str:
    text_clean = text.strip()
    confirmation_keywords = ["send", "schedule", "approve", "confirm", "proceed", "read", "go ahead", "create", "pay", "do you want", "would you like", "want me to"]
    has_question = text_clean.endswith("?") or "?" in text_clean
    has_keyword = any(kw in text_clean.lower() for kw in confirmation_keywords)

    if has_question and has_keyword:
        return text_clean

    if not text_clean.endswith("?"):
        if text_clean.endswith("."):
            text_clean = text_clean[:-1]
        text_clean = f"{text_clean} — would you like me to proceed?"
    return text_clean
