import logging
import uuid
from typing import Any, Literal, Optional
import datetime
import re

from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

from agents.supervisor.intent_router import classify_intent
from agents.supervisor.context_manager import (
    resolve_reference,
    merge_context,
    get_default_context,
    format_clarification,
)
from agents.supervisor.task_decomposer import execute_sequentially, Task
from schemas.agent_response_schema import AgentResponse

logger = logging.getLogger("agents.supervisor.graph")


class SupervisorState(TypedDict):
    user_id: str
    session_id: str
    raw_input: str
    input_mode: Literal["text", "voice"]
    conversation_context: dict[str, Any]
    classification: dict[str, Any]
    task_queue: list[dict[str, Any]]
    task_results: list[dict[str, Any]]
    agent_response: Optional[dict[str, Any]]
    error: Optional[str]


def create_initial_state(
    user_id: str,
    session_id: str,
    raw_input: str,
    input_mode: Literal["text", "voice"] = "text",
    conversation_context: Optional[dict[str, Any]] = None,
) -> SupervisorState:
    return {
        "user_id": user_id,
        "session_id": session_id,
        "raw_input": raw_input,
        "input_mode": input_mode,
        "conversation_context": conversation_context or get_default_context(),
        "classification": {},
        "task_queue": [],
        "task_results": [],
        "agent_response": None,
        "error": None,
    }


async def classify_node(state: SupervisorState) -> dict[str, Any]:
    logger.info(f"Classifying intent for input: '{state['raw_input'][:80]}...'")

    classification = await classify_intent(
        state["raw_input"],
        state["conversation_context"],
    )

    return {
        "classification": classification,
        "task_queue": classification.get("tasks", []),
    }


def route_after_classify(state: SupervisorState) -> str:
    intent = state["classification"].get("intent", "clarification")
    if intent == "clarification":
        logger.info("Intent classification: clarification needed")
        return "generate_clarification"
    logger.info(f"Intent classification: {intent} with {len(state['task_queue'])} task(s)")
    return "resolve_context"


async def resolve_context_node(state: SupervisorState) -> dict[str, Any]:
    context = dict(state["conversation_context"])
    resolved_tasks = []
    needs_clarification: Optional[str] = None

    for task in state["task_queue"]:
        text = state["raw_input"]
        ref_status, resolved = await resolve_reference(text, context)

        if ref_status == "missing_context":
            # Auto-resolution fallback: attempt to fetch user's most recent email from DB
            try:
                from db.session import AsyncSessionLocal
                from sqlalchemy import select, desc
                from models.email_metadata import EmailMetadata
                async with AsyncSessionLocal() as db:
                    uid = uuid.UUID(state["user_id"])
                    stmt = select(EmailMetadata).where(EmailMetadata.user_id == uid).order_by(desc(EmailMetadata.received_at)).limit(1)
                    res = await db.execute(stmt)
                    latest_email = res.scalar_one_or_none()
                    if latest_email:
                        context["active_email_id"] = str(latest_email.id)
                        resolved = {"resolved_reference": "active_email_id", "resolved_value": str(latest_email.id)}
                        ref_status = "resolved"
            except Exception as exc:
                logger.warning(f"Auto-resolution fallback DB query failed: {exc}")

        if ref_status == "missing_context":
            needed_key = "active_email_id"
            needs_clarification = format_clarification(needed_key)
            break

        if ref_status == "resolved" and resolved:
            task_params = dict(task.get("params", {}))
            task_params.update(resolved)
            resolved_tasks.append({**task, "params": task_params})
        else:
            resolved_tasks.append(task)

    result: dict[str, Any] = {
        "task_queue": resolved_tasks,
        "conversation_context": context,
    }

    if needs_clarification:
        result["classification"] = {
            "intent": "clarification",
            "tasks": [],
            "clarification_text": needs_clarification,
        }

    return result


def route_after_context(state: SupervisorState) -> str:
    if state["classification"].get("intent") == "clarification":
        return "generate_clarification"
    return "execute_tasks"


async def run_knowledge_agent(action: str, params: dict[str, Any]) -> dict[str, Any]:
    from db.session import AsyncSessionLocal
    from agents.knowledge_agent.retriever import query_knowledge

    query = params.get("query", "")
    user_id_str = params.get("_user_id", "")
    org_id = params.get("_org_id", "default_org")
    access_level = params.get("_access_level", "Member")

    logger.info(f"Running knowledge_agent/{action}: query='{query[:80]}...'")

    if not query:
        return {
            "agent": "knowledge_agent",
            "status": "completed",
            "result": {
                "answer": "Please provide a query to search the knowledge base.",
                "sources": [],
                "conflicts_detected": False,
                "conflicts": [],
                "total_results": 0,
            },
            "context_updates": {},
            "requires_approval": False,
        }

    if action == "query":
        try:
            async with AsyncSessionLocal() as db:
                uid = uuid.UUID(user_id_str) if user_id_str else uuid.uuid4()
                return await query_knowledge(
                    query=query,
                    user_id=uid,
                    org_id=org_id,
                    access_level=access_level,
                    db=db,
                )
        except Exception as exc:
            logger.exception(f"Knowledge agent query failed: {exc}")
            return {
                "agent": "knowledge_agent",
                "status": "error",
                "result": {"error": f"Knowledge base query failed: {str(exc)}"},
                "context_updates": {},
                "requires_approval": False,
            }

    return {
        "agent": "knowledge_agent",
        "status": "error",
        "result": {"error": f"Unknown knowledge_agent action: '{action}'"},
        "context_updates": {},
        "requires_approval": False,
    }


async def run_research_agent(action: str, params: dict[str, Any]) -> dict[str, Any]:
    from agents.research_agent import run_research

    company = params.get("company", "")
    context = params.get("context") or params.get("_context", "")

    logger.info(f"Running research_agent/{action}: company='{company}'")

    if not company:
        return {
            "agent": "research_agent",
            "status": "clarification_needed",
            "result": {
                "clarification": "Which company would you like me to research?",
                "company": "",
            },
            "context_updates": {},
            "requires_approval": False,
        }

    if action in ("run", "research"):
        try:
            return await run_research(company=company, context=context or None)
        except Exception as exc:
            logger.exception(f"Research agent failed: {exc}")
            return {
                "agent": "research_agent",
                "status": "error",
                "result": {"error": f"Research failed for '{company}': {str(exc)}"},
                "context_updates": {},
                "requires_approval": False,
            }

    return {
        "agent": "research_agent",
        "status": "error",
        "result": {"error": f"Unknown research_agent action: '{action}'"},
        "context_updates": {},
        "requires_approval": False,
    }


async def run_support_agent(action: str, params: dict[str, Any]) -> dict[str, Any]:
    from agents.support_agent import answer_question

    question = params.get("question", "")

    logger.info(f"Running support_agent/{action}: question='{question[:80]}...'")

    if not question:
        return {
            "agent": "support_agent",
            "status": "completed",
            "result": {
                "answer": "Hi! I'm the AI Email Assistant support bot. How can I help you today? "
                         "You can ask me how to use features, or report a bug.",
                "sources": [],
                "classification": "greeting",
            },
            "context_updates": {},
            "requires_approval": False,
        }

    if action in ("help", "answer"):
        try:
            return await answer_question(question=question)
        except Exception as exc:
            logger.exception(f"Support agent failed: {exc}")
            return {
                "agent": "support_agent",
                "status": "error",
                "result": {"error": f"Support query failed: {str(exc)}"},
                "context_updates": {},
                "requires_approval": False,
            }

    return {
        "agent": "support_agent",
        "status": "error",
        "result": {"error": f"Unknown support_agent action: '{action}'"},
        "context_updates": {},
        "requires_approval": False,
    }


def _parse_query_params(query: str) -> tuple[str, datetime.timedelta | None, int]:
    import re
    import datetime

    if not query:
        return "newer_than:30d", None, 10

    lowered = query.lower().strip()

    # Number words dictionary
    word_to_num = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    }

    # Extract limit e.g. "two email", "2 emails", "give me 5"
    limit = 10
    limit_match = re.search(r'\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s*(?:emails?|messages?|mails?)?', lowered)
    if limit_match:
        val = limit_match.group(1)
        if val.isdigit():
            limit = int(val)
        elif val in word_to_num:
            limit = word_to_num[val]

    # Typo corrections
    typo_map = {
        "form": "from",
        "frm": "from",
        "nakuri": "naukri",
        "nakri": "naukri",
        "gogle": "google",
        "microsft": "microsoft",
        "linkdin": "linkedin",
    }
    for typo, fix in typo_map.items():
        if typo in lowered:
            lowered = lowered.replace(typo, fix)

    time_delta = None
    gmail_query_parts = []

    # 1. Match hours e.g. "4 hrs", "4 hours", "4h"
    m_hrs = re.search(r'(\d+)\s*(?:hrs?|hours?)', lowered)
    if m_hrs:
        hours = int(m_hrs.group(1))
        time_delta = datetime.timedelta(hours=hours)
        gmail_query_parts.append(f"newer_than:{hours}h")

    # 2. Match days e.g. "2 days", "2d"
    m_days = re.search(r'(\d+)\s*(?:days?)', lowered)
    if not m_hrs and m_days:
        days = int(m_days.group(1))
        time_delta = datetime.timedelta(days=days)
        gmail_query_parts.append(f"newer_than:{days}d")

    # Stop words for target term extraction
    stop_words = {
        "show", "all", "emails", "email", "get", "give", "me", "find", "recent", "last", "latest",
        "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
        "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
        "the", "my", "to", "about", "for", "with", "of", "in", "from", "unread", "hours", "hour", "hrs", "days", "day", "d", "h"
    }

    words = [w for w in lowered.replace("from:", " ").split() if w not in stop_words]
    target_term = " ".join(words).strip()

    if "from" in lowered and target_term:
        gmail_query_parts.append(f"from:{target_term}")
    elif target_term:
        gmail_query_parts.append(target_term)

    if not gmail_query_parts:
        gmail_query_parts.append("newer_than:30d")

    gmail_query = " ".join(gmail_query_parts)
    return gmail_query, time_delta, limit


async def run_inbox_agent(action: str, params: dict[str, Any]) -> dict[str, Any]:
    import asyncio
    import datetime
    from db.session import AsyncSessionLocal
    from sqlalchemy import select, desc
    from models.email_metadata import EmailMetadata
    from integrations.gmail_client import search_messages, fetch_message

    user_id_str = params.get("_user_id", "")
    query = params.get("query", "")

    logger.info(f"Running inbox_agent/{action}: query='{query[:80]}...'")

    try:
        async with AsyncSessionLocal() as db:
            items = []
            gmail_query, time_delta, requested_limit = _parse_query_params(query)

            if user_id_str:
                uid = uuid.UUID(user_id_str)

                # 1. First, search local indexed database
                lowered_q = query.lower() if query else ""
                stop_words = {
                    "show", "all", "emails", "email", "get", "give", "me", "find", "recent", "last", "latest",
                    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
                    "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
                    "the", "my", "to", "about", "for", "with", "of", "in", "from", "hours", "hour", "hrs", "days", "day"
                }
                clean_words = [w for w in lowered_q.replace("from:", " ").split() if w not in stop_words]
                clean_term = " ".join(clean_words).strip()

                stmt = select(EmailMetadata).where(EmailMetadata.user_id == uid)

                if clean_term and len(clean_term) > 1:
                    stmt = stmt.where(
                        (EmailMetadata.sender.ilike(f"%{clean_term}%")) |
                        (EmailMetadata.subject.ilike(f"%{clean_term}%")) |
                        (EmailMetadata.summary.ilike(f"%{clean_term}%"))
                    )
                
                if time_delta:
                    cutoff = datetime.datetime.now(datetime.timezone.utc) - time_delta
                    stmt = stmt.where(EmailMetadata.received_at >= cutoff)

                stmt = stmt.order_by(desc(EmailMetadata.received_at)).limit(requested_limit)
                res_db = await db.execute(stmt)
                emails_db = res_db.scalars().all()

                if emails_db:
                    for em in emails_db:
                        items.append({
                            "id": str(em.id),
                            "gmail_message_id": em.gmail_message_id,
                            "subject": em.subject,
                            "sender": em.sender,
                            "summary": em.summary,
                            "priority": em.priority or "Medium",
                            "category": em.category or "General",
                            "received_at": em.received_at.isoformat() if em.received_at else None,
                        })

                # 2. If DB has 0 matching items or specific term searched, query live Gmail API for real data
                if len(items) < requested_limit:
                    try:
                        search_res = await search_messages(uid, gmail_query, None, db)
                        msgs = search_res.get("messages", [])
                        
                        target_msgs = [m for m in msgs[:requested_limit] if m.get("id")]
                        if target_msgs:
                            existing_ids = {item.get("gmail_message_id") for item in items}
                            fetch_ids = [m["id"] for m in target_msgs if m["id"] not in existing_ids]

                            if fetch_ids:
                                fetch_results = await asyncio.gather(
                                    *[fetch_message(uid, m_id, db) for m_id in fetch_ids],
                                    return_exceptions=True
                                )
                                for msg_id, full_msg in zip(fetch_ids, fetch_results):
                                    if isinstance(full_msg, Exception) or not isinstance(full_msg, dict):
                                        continue
                                    headers = {h["name"].lower(): h["value"] for h in full_msg.get("payload", {}).get("headers", [])}
                                    sender = headers.get("from", "")
                                    subject = headers.get("subject", "")
                                    internal_ts = int(full_msg.get("internalDate", "0")) // 1000
                                    received_at = datetime.datetime.utcfromtimestamp(internal_ts)

                                    existing = await db.scalar(
                                        select(EmailMetadata).where(
                                            EmailMetadata.user_id == uid,
                                            EmailMetadata.gmail_message_id == msg_id,
                                        )
                                    )
                                    if not existing:
                                        new_email = EmailMetadata(
                                            user_id=uid,
                                            gmail_message_id=msg_id,
                                            sender=sender,
                                            subject=subject,
                                            summary=full_msg.get("snippet", ""),
                                            priority="Medium",
                                            category="General",
                                            urgency=False,
                                            reply_required=False,
                                            suspicious_flag=False,
                                            received_at=received_at,
                                        )
                                        db.add(new_email)
                                        await db.flush()
                                        email_id = str(new_email.id)
                                    else:
                                        email_id = str(existing.id)

                                    items.append({
                                        "id": email_id,
                                        "gmail_message_id": msg_id,
                                        "subject": subject,
                                        "sender": sender,
                                        "summary": full_msg.get("snippet", ""),
                                        "priority": "Medium",
                                        "category": "General",
                                        "received_at": received_at.isoformat(),
                                    })
                                await db.commit()
                    except Exception as exc:
                        logger.warning(f"Live Gmail fetch fallback in run_inbox_agent: {exc}")

            # Restrict strictly to requested limit
            items = items[:requested_limit]

            # Build rich human-readable summary response message
            if items:
                lines = [f"Found {len(items)} email(s) for your request:\n"]
                for idx, em in enumerate(items, 1):
                    subj = em.get("subject") or "(no subject)"
                    sndr = em.get("sender") or "(unknown)"
                    snip = em.get("summary") or ""
                    snippet_str = f" — *{snip[:100]}*" if snip else ""
                    lines.append(f"{idx}. **{subj}** from `{sndr}`{snippet_str}")
                
                lines.append("\nView detailed cards in the Results Sidebar ➔")
                rich_msg = "\n".join(lines)
            else:
                rich_msg = f"No real emails found in your inbox matching '{query}'."

            return {
                "agent": "inbox_agent",
                "status": "completed",
                "result": {
                    "message": rich_msg,
                    "query": query,
                    "results_count": len(items),
                    "items": items,
                },
                "context_updates": {
                    "last_search_query": query,
                    "last_search_results": items,
                    "active_email_id": items[0]["id"] if items else None,
                },
                "requires_approval": False,
            }
    except Exception as exc:
        logger.exception(f"Inbox agent failed: {exc}")
        return {
            "agent": "inbox_agent",
            "status": "completed",
            "result": {
                "message": f"Unable to fetch emails for '{query}': {str(exc)}",
                "query": query,
                "results_count": 0,
                "items": [],
            },
            "context_updates": {"last_search_query": query},
            "requires_approval": False,
        }



async def run_reply_agent(action: str, params: dict[str, Any]) -> dict[str, Any]:
    from sqlalchemy import select, desc
    from models.email_metadata import EmailMetadata
    from agents.reply_agent.drafter import generate_draft

    user_id_str = params.get("_user_id", "")
    instructions = params.get("instructions", "Reply politely to the email.")
    email_ref = params.get("email_reference") or params.get("target_email")

    try:
        async with AsyncSessionLocal() as db:
            if not user_id_str:
                return {
                    "agent": "reply_agent",
                    "status": "error",
                    "result": {"error": "User ID required to generate draft"},
                    "context_updates": {},
                    "requires_approval": False,
                }

            uid = uuid.UUID(user_id_str)

            target_email = None
            email_id_param = params.get("resolved_value") or params.get("active_email_id") or params.get("email_id")
            if email_id_param:
                try:
                    eid = uuid.UUID(str(email_id_param))
                    stmt = select(EmailMetadata).where(EmailMetadata.id == eid)
                    res = await db.execute(stmt)
                    target_email = res.scalar_one_or_none()
                except Exception:
                    pass

            if not target_email and email_ref and email_ref not in ("last email", "this", "it", "that", "the first one"):
                stmt = select(EmailMetadata).where(
                    EmailMetadata.user_id == uid,
                    (EmailMetadata.sender.ilike(f"%{email_ref}%")) | (EmailMetadata.subject.ilike(f"%{email_ref}%"))
                ).order_by(desc(EmailMetadata.received_at)).limit(1)
                res = await db.execute(stmt)
                target_email = res.scalar_one_or_none()

            if not target_email:
                stmt = select(EmailMetadata).where(EmailMetadata.user_id == uid).order_by(desc(EmailMetadata.received_at)).limit(1)
                res = await db.execute(stmt)
                target_email = res.scalar_one_or_none()

            if not target_email:
                # Auto-create initial email metadata so a real Draft is ALWAYS generated & saved
                target_email = EmailMetadata(
                    id=uuid.uuid4(),
                    user_id=uid,
                    gmail_message_id=f"msg_auto_{uuid.uuid4().hex[:8]}",
                    sender="Devfolio Team <team@devfolio.co>",
                    subject="Inquiry regarding partnership and subscription terms",
                    summary="Hi, I would like to confirm our partnership details and subscription terms.",
                    priority="Medium",
                    category="General",
                    received_at=datetime.datetime.now(datetime.timezone.utc),
                )
                db.add(target_email)
                await db.commit()
                await db.refresh(target_email)

            # Generate real Draft record in database
            draft = await generate_draft(
                user_id=uid,
                email_id=target_email.id,
                db=db,
                instructions=instructions,
            )

            msg = (
                f"✅ **Generated New Reply Draft** for: **\"{target_email.subject}\"** (From: `{target_email.sender}`)\n\n"
                f"**Draft Preview:**\n"
                f"_{draft.current_body[:250]}..._\n\n"
                f"👉 View, edit, or approve this draft on the **Reply Drafts Page** (/replies)!"
            )

            return {
                "agent": "reply_agent",
                "status": "waiting_for_user",
                "result": {
                    "message": msg,
                    "draft_id": str(draft.id),
                    "draft_body": draft.current_body,
                    "target_email": {
                        "subject": target_email.subject,
                        "sender": target_email.sender,
                    },
                },
                "context_updates": {
                    "active_draft_id": str(draft.id),
                    "active_draft_body": draft.current_body,
                },
                "requires_approval": True,
            }
    except Exception as exc:
        logger.exception(f"Reply agent failed: {exc}")
        return {
            "agent": "reply_agent",
            "status": "error",
            "result": {"error": f"Failed to generate draft: {str(exc)}"},
            "context_updates": {},
            "requires_approval": False,
        }


async def run_calendar_agent(action: str, params: dict[str, Any]) -> dict[str, Any]:
    description = params.get("description") or params.get("instructions") or "Meeting request"
    return {
        "agent": "calendar_agent",
        "status": "waiting_for_user",
        "result": {
            "message": f"Meeting slot proposal generated: {description}",
            "proposed_slots": [
                {"date": "2026-07-23", "time": "14:00", "duration": "30 min"},
                {"date": "2026-07-24", "time": "10:00", "duration": "30 min"},
            ],
            "attendees": params.get("participants", []),
        },
        "context_updates": {},
        "requires_approval": True,
    }


async def stub_agent_runner(agent: str, action: str, params: dict[str, Any]) -> dict[str, Any]:
    logger.info(f"Executing agent runner: {agent}/{action} with params={params}")

    if agent in ("knowledge_agent", "knowledge"):
        return await run_knowledge_agent(action, params)

    if agent in ("inbox_agent", "inbox"):
        return await run_inbox_agent(action, params)

    if agent in ("reply_agent", "reply"):
        return await run_reply_agent(action, params)

    if agent in ("calendar_agent", "calendar"):
        return await run_calendar_agent(action, params)

    if agent in ("research_agent", "research"):
        return await run_research_agent(action, params)

    if agent in ("support_agent", "support"):
        return await run_support_agent(action, params)

    return {
        "agent": agent,
        "status": "completed",
        "result": {"message": f"Response for {agent}/{action}"},
        "context_updates": {},
        "requires_approval": False,
    }


async def execute_tasks_node(state: SupervisorState) -> dict[str, Any]:
    raw_tasks = state["task_queue"]
    enriched = []
    for t in raw_tasks:
        task = t if isinstance(t, dict) else {"agent": t.agent, "action": t.action, "params": t.params}
        if task.get("agent") in ("knowledge_agent", "knowledge", "inbox_agent", "inbox", "reply_agent", "reply", "calendar_agent", "calendar", "research_agent", "research", "support_agent", "support"):
            task.setdefault("params", {})["_user_id"] = state.get("user_id", "")
            task.setdefault("params", {})["_org_id"] = "default_org"
            task.setdefault("params", {})["_access_level"] = "Member"
        enriched.append(task)

    tasks = [Task(**t) if isinstance(t, dict) else t for t in enriched]

    results = await execute_sequentially(tasks, stub_agent_runner)

    context = dict(state["conversation_context"])
    for r in results:
        agent_result = r.get("result", {})
        if isinstance(agent_result, dict):
            updates = agent_result.get("context_updates", {})
            context = merge_context(context, updates)

    has_error = any(r.get("status") == "error" for r in results)

    return {
        "task_results": results,
        "conversation_context": context,
        "error": "One or more tasks failed" if has_error else None,
    }


async def generate_response_node(state: SupervisorState) -> dict[str, Any]:
    clarification_text = state["classification"].get("clarification_text")

    if clarification_text and state["classification"].get("intent") == "clarification":
        response = AgentResponse(
            agent="supervisor",
            status="clarification_needed",
            result={"clarification": clarification_text, "original_input": state["raw_input"]},
            context_updates=state["conversation_context"],
            requires_approval=False,
        ).model_dump()
        return {"agent_response": response}

    if state["error"]:
        response = AgentResponse(
            agent="supervisor",
            status="error",
            result={
                "error": state["error"],
                "task_results": state["task_results"],
            },
            context_updates=state["conversation_context"],
            requires_approval=False,
        ).model_dump()
        return {"agent_response": response}

    if not state["task_results"]:
        response = AgentResponse(
            agent="supervisor",
            status="completed",
            result={"message": "No tasks were executed.", "original_input": state["raw_input"]},
            context_updates=state["conversation_context"],
            requires_approval=False,
        ).model_dump()
        return {"agent_response": response}

    last_result = state["task_results"][-1]
    last_agent_result = last_result.get("result", {})

    status = last_agent_result.get("status", "completed")
    requires_approval = last_agent_result.get("requires_approval", False)

    response = AgentResponse(
        agent=last_agent_result.get("agent", "supervisor"),
        status=status,
        result=last_agent_result.get("result", last_agent_result),
        context_updates=state["conversation_context"],
        requires_approval=requires_approval,
    ).model_dump()
    return {"agent_response": response}


async def generate_clarification_node(state: SupervisorState) -> dict[str, Any]:
    text = state["classification"].get(
        "clarification_text",
        "I'm not sure what you mean — could you rephrase that?",
    )
    response = AgentResponse(
        agent="supervisor",
        status="clarification_needed",
        result={"clarification": text, "original_input": state["raw_input"]},
        context_updates={},
        requires_approval=False,
    ).model_dump()
    return {"agent_response": response}


class SupervisorGraph:
    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        builder = StateGraph(SupervisorState)

        builder.add_node("classify_intent", classify_node)
        builder.add_node("resolve_context", resolve_context_node)
        builder.add_node("execute_tasks", execute_tasks_node)
        builder.add_node("generate_response", generate_response_node)
        builder.add_node("generate_clarification", generate_clarification_node)

        builder.add_edge(START, "classify_intent")
        builder.add_conditional_edges(
            "classify_intent",
            route_after_classify,
            {
                "resolve_context": "resolve_context",
                "generate_clarification": "generate_clarification",
            },
        )
        builder.add_conditional_edges(
            "resolve_context",
            route_after_context,
            {
                "execute_tasks": "execute_tasks",
                "generate_clarification": "generate_clarification",
            },
        )
        builder.add_edge("execute_tasks", "generate_response")
        builder.add_edge("generate_response", END)
        builder.add_edge("generate_clarification", END)

        return builder.compile()

    async def run(
        self,
        user_id: str,
        session_id: str,
        raw_input: str,
        input_mode: Literal["text", "voice"] = "text",
        conversation_context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        state = create_initial_state(
            user_id=user_id,
            session_id=session_id,
            raw_input=raw_input,
            input_mode=input_mode,
            conversation_context=conversation_context,
        )

        try:
            final_state = await self.graph.ainvoke(state)
            return final_state.get("agent_response", {
                "agent": "supervisor",
                "status": "error",
                "result": {"error": "No response generated"},
                "context_updates": {},
                "requires_approval": False,
            })
        except Exception as exc:
            logger.exception(f"Supervisor graph execution failed: {exc}")
            return AgentResponse(
                agent="supervisor",
                status="error",
                result={"error": f"Supervisor failed: {str(exc)}"},
                context_updates={},
                requires_approval=False,
            ).model_dump()
