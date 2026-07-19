import logging
from typing import Any, Optional

logger = logging.getLogger("agents.supervisor.context_manager")

DEFAULT_CONTEXT: dict[str, Any] = {
    "active_email_id": None,
    "active_thread_id": None,
    "active_draft_id": None,
    "last_search_query": None,
    "last_search_results": [],
    "last_meeting_preview_id": None,
}

REFERENCE_PATTERNS = {
    "it": "active_email_id",
    "this email": "active_email_id",
    "that email": "active_email_id",
    "the email": "active_email_id",
    "the first one": "last_search_results_index_0",
    "the second one": "last_search_results_index_1",
    "the third one": "last_search_results_index_2",
    "the draft": "active_draft_id",
    "this draft": "active_draft_id",
    "that draft": "active_draft_id",
    "the meeting": "last_meeting_preview_id",
    "this meeting": "last_meeting_preview_id",
    "that meeting": "last_meeting_preview_id",
}


def get_default_context() -> dict[str, Any]:
    return dict(DEFAULT_CONTEXT)


def merge_context(
    current: dict[str, Any],
    updates: dict[str, Any],
) -> dict[str, Any]:
    merged = dict(current)
    for key, value in updates.items():
        if value is not None:
            merged[key] = value
    return merged


async def resolve_reference(
    text: str,
    context: dict[str, Any],
) -> tuple[str, Optional[dict[str, Any]]]:
    lowered = text.lower().strip()

    exact = REFERENCE_PATTERNS.get(lowered)
    if exact is not None:
        if exact.startswith("last_search_results_index_"):
            idx = int(exact.rsplit("_", 1)[1])
            results = context.get("last_search_results", [])
            if idx < len(results):
                return "resolved", {"resolved_email": results[idx]}
            return "ambiguous", None

        resolved_value = context.get(exact)
        if resolved_value is not None:
            return "resolved", {"resolved_reference": exact, "resolved_value": resolved_value}
        return "missing_context", None

    if "reply to it" in lowered or "reply to that" in lowered:
        email_id = context.get("active_email_id")
        if email_id:
            return "resolved", {"resolved_reference": "active_email_id", "resolved_value": email_id}
        return "missing_context", None

    if "schedule" in lowered and ("it" in lowered or "this" in lowered or "that" in lowered):
        email_id = context.get("active_email_id")
        if email_id:
            return "resolved", {"resolved_reference": "active_email_id", "resolved_value": email_id}
        return "missing_context", None

    return "unresolved", None


def format_clarification(missing_ref: str) -> str:
    if missing_ref == "active_email_id":
        return "I don't have an email in context right now — which one would you like to act on?"
    if missing_ref == "active_draft_id":
        return "I don't see an active draft — which email would you like to reply to?"
    if missing_ref == "last_meeting_preview_id":
        return "I don't have a meeting preview in context — which meeting would you like to schedule?"
    return "I'm not sure what you're referring to — could you be more specific?"
