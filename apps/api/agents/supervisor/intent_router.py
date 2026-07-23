import json
import logging
from typing import Any, Optional

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from core.config import settings
from agents.supervisor.prompts import SYSTEM_PROMPT, CLARIFICATION_PROMPT

logger = logging.getLogger("agents.supervisor.intent_router")


class InboxSearchParams(BaseModel):
    query: str = Field(description="Natural language search query for emails")
    page_token: Optional[str] = Field(None, description="Pagination token")


class InboxReadParams(BaseModel):
    email_reference: str = Field(description="Reference to which email to open (index, sender, or subject)")


class ReplyDraftParams(BaseModel):
    email_reference: str = Field(description="The email being replied to")
    instructions: str = Field(description="Instructions for the reply tone, length, content")
    knowledge_query: Optional[str] = Field(None, description="Optional query for knowledge base context")


class ReplyEditParams(BaseModel):
    instructions: str = Field(description="Edit instructions like 'shorten it', 'make it more professional'")


class CalendarScheduleParams(BaseModel):
    email_reference: Optional[str] = Field(None, description="Reference to the email with scheduling request")
    date_time: Optional[str] = Field(None, description="Proposed date/time for the meeting")
    duration_minutes: Optional[int] = Field(60, description="Meeting duration in minutes")
    participants: Optional[list[str]] = Field(None, description="List of participant email addresses")
    title: Optional[str] = Field(None, description="Meeting title")


class KnowledgeQueryParams(BaseModel):
    query: str = Field(description="The question to ask the knowledge base")


class ResearchParams(BaseModel):
    company: str = Field(description="Company name to research")
    context: Optional[str] = Field(None, description="Additional context about the research need")


class SupportParams(BaseModel):
    question: str = Field(description="The user's product help question")


AGENT_TOOL_DEFINITIONS: dict[str, tuple[type[BaseModel], str]] = {
    "inbox_agent_search": (InboxSearchParams, "Search and find emails in the user's inbox using natural language"),
    "inbox_agent_read": (InboxReadParams, "Open and read a specific email with full content and thread context"),
    "reply_agent_draft": (ReplyDraftParams, "Generate a reply draft for an email, grounded in thread context and knowledge base"),
    "reply_agent_edit": (ReplyEditParams, "Edit the current reply draft according to instructions"),
    "calendar_agent_schedule": (CalendarScheduleParams, "Schedule a meeting by checking availability and creating a calendar event"),
    "knowledge_agent_query": (KnowledgeQueryParams, "Query the company knowledge base to answer a question"),
    "research_agent_run": (ResearchParams, "Research a company and produce a structured market report"),
    "support_agent_help": (SupportParams, "Answer product questions or help with onboarding"),
}

CLARIFICATION_MARKER = "CLARIFICATION_NEEDED"


async def classify_intent(
    raw_input: str,
    context: dict[str, Any],
    llm: Optional[ChatOpenAI] = None,
) -> dict[str, Any]:
    lowered = raw_input.lower().strip()
    
    # Ultra-fast path (0.1ms) for common email search patterns
    email_kws = ["email", "emails", "inbox", "from", "unread", "recent", "past", "last", "hour", "day", "get", "give", "show", "find", "search"]
    if any(kw in lowered for kw in email_kws):
        if not any(kw in lowered for kw in ["reply", "draft", "schedule", "meeting", "calendar"]):
            logger.info(f"Fast-path matched email search query: '{raw_input}'")
            return {
                "tasks": [{
                    "agent": "inbox_agent",
                    "action": "agent_search",
                    "params": {"query": raw_input}
                }],
                "intent": "inbox_agent_search",
                "clarification_text": None,
            }

    if llm is None:
        llm = _default_llm()

    system_msg = SYSTEM_PROMPT + "\n\n" + CLARIFICATION_PROMPT

    context_summary = _summarize_context(context)
    user_msg = f"User command: '{raw_input}'\n\nCurrent context: {context_summary}"

    tools = _build_tool_definitions()

    try:
        response = llm.bind_tools(tools).invoke([
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ])

        return _parse_llm_response(response, tools)

    except Exception as exc:
        logger.exception(f"LLM intent classification failed: {exc}")
        return _fallback_classification(raw_input)


def _default_llm() -> ChatOpenAI:
    kwargs = {
        "model": getattr(settings, "OPENAI_MODEL_CLASSIFIER", "openrouter/auto") if settings.openai_base_url else "gpt-4o-mini",
        "temperature": 0.1,
        "api_key": settings.OPENAI_API_KEY,
    }
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    return ChatOpenAI(**kwargs)



def _summarize_context(context: dict[str, Any]) -> str:
    parts = []
    if context.get("active_email_id"):
        parts.append(f"active email ID: {context['active_email_id']}")
    if context.get("active_thread_id"):
        parts.append(f"active thread ID: {context['active_thread_id']}")
    if context.get("active_draft_id"):
        parts.append(f"active draft ID: {context['active_draft_id']}")
    if context.get("last_search_query"):
        parts.append(f"last search: '{context['last_search_query']}'")
    results_count = len(context.get("last_search_results", []))
    if results_count:
        parts.append(f"{results_count} emails in last search results")
    return "; ".join(parts) if parts else "no active context"


def _build_tool_definitions() -> list[dict[str, Any]]:
    tools = []
    for tool_name, (schema, description) in AGENT_TOOL_DEFINITIONS.items():
        schema_json = schema.model_json_schema()
        tools.append({
            "type": "function",
            "function": {
                "name": tool_name,
                "description": description,
                "parameters": schema_json,
            },
        })
    return tools


def _parse_llm_response(
    response,
    tools: list[dict[str, Any]],
) -> dict[str, Any]:
    tool_calls = getattr(response, "tool_calls", None) or []

    if not tool_calls:
        content = getattr(response, "content", "") or ""
        if not content:
            return {
                "intent": "clarification",
                "tasks": [],
                "clarification_text": "I didn't understand that — could you rephrase?",
            }
        return {
            "intent": "clarification",
            "tasks": [],
            "clarification_text": content,
        }

    tasks = []
    for tc in tool_calls:
        try:
            args = json.loads(tc.get("args", "{}") if isinstance(tc.get("args"), str) else json.dumps(tc.get("args", {})))
        except (json.JSONDecodeError, TypeError):
            args = {}

        agent_action = tc.get("name", "unknown")
        parts = agent_action.split("_", 1)
        agent = parts[0] if len(parts) > 0 else "unknown"
        action = parts[1] if len(parts) > 1 else agent_action

        tasks.append({
            "agent": agent,
            "action": action,
            "params": args,
        })

    if not tasks:
        return {
            "intent": "clarification",
            "tasks": [],
            "clarification_text": "I'm not sure what to do — could you clarify what you'd like?",
        }

    intent = "multi_step" if len(tasks) > 1 else "single"
    return {
        "intent": intent,
        "tasks": tasks,
        "clarification_text": None,
    }


def _fallback_classification(raw_input: str) -> dict[str, Any]:
    lowered = raw_input.lower().strip()

    # 1. Reply keywords / typos: reply, eply, rply, draft, compose, write, answer, respond
    if any(k in lowered for k in ["reply", "eply", "rply", "draft", "compose", "write", "answer", "respond"]):
        return {
            "intent": "single",
            "tasks": [{"agent": "reply_agent", "action": "draft", "params": {"instructions": raw_input, "email_reference": "last email"}}],
            "clarification_text": None,
        }

    # 2. Inbox search / fetch / recent keywords: search, find, show, list, open, read, email, mail, inbox, recent, past, give, get, fetch, unread, hrs, hours, from, form, frm
    if any(k in lowered for k in ["search", "find", "show", "list", "open", "read", "email", "mail", "inbox", "recent", "past", "give", "get", "fetch", "unread", "hrs", "hours", "from", "form", "frm"]):
        return {
            "intent": "single",
            "tasks": [{"agent": "inbox_agent", "action": "search", "params": {"query": raw_input}}],
            "clarification_text": None,
        }

    # 3. Schedule / Calendar keywords: schedule, meeting, meet, calendar, book, slot, appointment
    if any(k in lowered for k in ["schedule", "meeting", "meet", "calendar", "book", "slot", "appointment"]):
        return {
            "intent": "single",
            "tasks": [{"agent": "calendar_agent", "action": "schedule", "params": {"description": raw_input}}],
            "clarification_text": None,
        }

    # 4. Research keywords: research, investigate, company, look up
    if any(k in lowered for k in ["research", "investigate", "company", "look up"]):
        return {
            "intent": "single",
            "tasks": [{"agent": "research_agent", "action": "run", "params": {"company": raw_input}}],
            "clarification_text": None,
        }

    # 5. Knowledge query keywords: what, how, when, where, why, tell me, kb, knowledge, doc, policy
    if any(k in lowered for k in ["what", "how", "when", "where", "why", "tell me", "kb", "knowledge", "doc", "policy"]):
        return {
            "intent": "single",
            "tasks": [{"agent": "knowledge_agent", "action": "query", "params": {"query": raw_input}}],
            "clarification_text": None,
        }

    # 6. Support keywords: help, tutorial, guide, bug
    if any(k in lowered for k in ["help", "tutorial", "guide", "bug"]):
        return {
            "intent": "single",
            "tasks": [{"agent": "support_agent", "action": "help", "params": {"question": raw_input}}],
            "clarification_text": None,
        }

    return {
        "intent": "clarification",
        "tasks": [],
        "clarification_text": "I'm not sure what you'd like to do. Try something like: 'Show my unread emails', 'Reply to the last email', 'Schedule a meeting', or 'Research Acme Corp'.",
    }

