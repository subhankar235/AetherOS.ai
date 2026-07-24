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
    "same email": "active_email_id",
    "the same email": "active_email_id",
    "same one": "active_email_id",
    "the same one": "active_email_id",
    "the same": "active_email_id",
    "same": "active_email_id",
    "that same email": "active_email_id",
    "this same email": "active_email_id",
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


WORD_TO_INDEX: dict[str, int] = {
    "first": 0, "1st": 0, "one": 0,
    "second": 1, "2nd": 1, "two": 1,
    "third": 2, "3rd": 2, "three": 2,
    "fourth": 3, "4th": 3, "four": 3,
    "fifth": 4, "5th": 4, "five": 4,
    "sixth": 5, "6th": 5, "six": 5,
    "seventh": 6, "7th": 6, "seven": 6,
    "eighth": 7, "8th": 7, "eight": 7,
    "ninth": 8, "9th": 8, "nine": 8,
    "tenth": 9, "10th": 9, "ten": 9,
}


async def resolve_reference(
    text: str,
    context: dict[str, Any],
) -> tuple[str, Optional[dict[str, Any]]]:
    import re
    lowered = text.lower().strip()
    last_results = context.get("last_search_results", [])

    # 1. Check for "last", "last email", "the last email", "last one", "the last one"
    last_keywords = ["last email", "the last email", "last one", "the last one", "last"]
    if any(re.search(r'\b' + re.escape(k) + r'\b', lowered) for k in last_keywords):
        if last_results and len(last_results) > 0:
            target = last_results[-1]
            target_id = target.get("id") if isinstance(target, dict) else str(target)
            return "resolved", {
                "resolved_reference": "active_email_id",
                "resolved_value": target_id,
                "resolved_email": target,
                "email_reference": target.get("subject") if isinstance(target, dict) else None
            }
        active_email = context.get("active_email_id")
        if active_email:
            return "resolved", {"resolved_reference": "active_email_id", "resolved_value": active_email}

    # 2. Check numeric ordinal index references (e.g. "4 th email", "4th email", "email 4", "email #4", "number 5", "for 4")
    num_match = re.search(r'(?:email|number|no\.?|#)\s*#?\s*(\d+)', lowered)
    if not num_match:
        num_match = re.search(r'\b(\d+)\s*(?:st|nd|rd|th)?\s*(?:email|one|\b)', lowered)
    if not num_match:
        num_match = re.search(r'\b(?:for|to|about|on)\s+(\d+)\b', lowered)

    if num_match:
        idx = int(num_match.group(1)) - 1  # 1-indexed to 0-indexed
        if last_results and 0 <= idx < len(last_results):
            target = last_results[idx]
            target_id = target.get("id") if isinstance(target, dict) else str(target)
            return "resolved", {
                "resolved_reference": "active_email_id",
                "resolved_value": target_id,
                "resolved_email": target,
                "email_reference": target.get("subject") if isinstance(target, dict) else None
            }

    # 3. Check word ordinals (first, second, third ... tenth)
    for word, idx in WORD_TO_INDEX.items():
        pattern = r'\b(?:the\s+)?' + re.escape(word) + r'\s+(?:email|one)?\b|\bemail\s+' + re.escape(word) + r'\b'
        if re.search(pattern, lowered):
            if last_results and 0 <= idx < len(last_results):
                target = last_results[idx]
                target_id = target.get("id") if isinstance(target, dict) else str(target)
                return "resolved", {
                    "resolved_reference": "active_email_id",
                    "resolved_value": target_id,
                    "resolved_email": target,
                    "email_reference": target.get("subject") if isinstance(target, dict) else None
                }

    # 4. Exact pattern lookup
    exact = REFERENCE_PATTERNS.get(lowered)
    if exact is not None:
        if exact.startswith("last_search_results_index_"):
            idx = int(exact.rsplit("_", 1)[1])
            if idx < len(last_results):
                target = last_results[idx]
                target_id = target.get("id") if isinstance(target, dict) else str(target)
                return "resolved", {
                    "resolved_reference": "active_email_id",
                    "resolved_value": target_id,
                    "resolved_email": target,
                    "email_reference": target.get("subject") if isinstance(target, dict) else None
                }
            return "ambiguous", None

        resolved_value = context.get(exact)
        if resolved_value is not None:
            return "resolved", {"resolved_reference": exact, "resolved_value": resolved_value}

    # 5. Heuristic check for email pronouns/actions (e.g. "this", "it", "that", "same", "same email", "reply", "draft")
    email_pronoun_keywords = [
        "this", "it", "that", "same", "the same", "same email", "the same email", "same one", "the same one",
        "for this", "the email", "for it", "make draft", "draft", "reply"
    ]
    if any(kw in lowered for kw in email_pronoun_keywords):
        if last_results:
            first_res = last_results[0]
            first_id = first_res.get("id") if isinstance(first_res, dict) else first_res
            return "resolved", {
                "resolved_reference": "active_email_id",
                "resolved_value": first_id,
                "resolved_email": first_res if isinstance(first_res, dict) else None
            }

        active_email = context.get("active_email_id")
        if active_email:
            return "resolved", {"resolved_reference": "active_email_id", "resolved_value": active_email}

        if any(term in lowered for term in ["draft", "reply", "this", "it"]):
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
