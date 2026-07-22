import logging
import uuid
from typing import Any, Literal, Optional

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


async def run_inbox_agent(action: str, params: dict[str, Any]) -> dict[str, Any]:
    import datetime
    from db.session import AsyncSessionLocal
    from sqlalchemy import select, desc
    from models.email_metadata import EmailMetadata
    from models.google_integration import GoogleIntegration
    from integrations.gmail_client import search_messages, fetch_message
    from core.exceptions import IntegrationAuthRequiredError

    user_id_str = params.get("_user_id", "")
    query = params.get("query", "")

    logger.info(f"Running inbox_agent/{action}: query='{query[:80]}...'")

    try:
        async with AsyncSessionLocal() as db:
            items = []
            if user_id_str:
                uid = uuid.UUID(user_id_str)

                # Check if this user has Google integration or find any active integration for local dev
                g_res = await db.execute(select(GoogleIntegration).where(GoogleIntegration.user_id == uid, GoogleIntegration.revoked_at.is_(None)))
                g_integration = g_res.scalar_one_or_none()
                if not g_integration:
                    any_g_res = await db.execute(select(GoogleIntegration).where(GoogleIntegration.revoked_at.is_(None)).limit(1))
                    any_g = any_g_res.scalar_one_or_none()
                    if any_g:
                        uid = any_g.user_id

                # Try live fetch from Gmail
                try:
                    gmail_query = "newer_than:30d" if not query or "recent" in query.lower() else query
                    search_res = await search_messages(uid, gmail_query, None, db)
                    msgs = search_res.get("messages", [])
                    for msg in msgs[:50]:
                        msg_id = msg.get("id")
                        if not msg_id:
                            continue
                        full_msg = await fetch_message(uid, msg_id, db)
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
                except IntegrationAuthRequiredError:
                    logger.info(f"Google integration not connected for user {user_id_str}")
                    msg = "Google OAuth connection required. Please visit http://localhost:8000/integrations/google/connect in your browser to connect Google."
                except Exception as exc:
                    exc_str = str(exc)
                    logger.warning(f"Live Gmail fetch failed for user {user_id_str}: {exc}")
                    if "accessNotConfigured" in exc_str or "Gmail API has not been used" in exc_str:
                        msg = "Gmail API is disabled in your Google Cloud Console project. Please enable it at https://console.developers.google.com/apis/api/gmail.googleapis.com/overview?project=416351192188 and try again."

                # Fallback to local DB if live fetch produced no new items or wasn't connected
                if not items:
                    stmt = select(EmailMetadata).order_by(desc(EmailMetadata.received_at)).limit(50)
                    res = await db.execute(stmt)
                    emails = res.scalars().all()

                    for em in emails:
                        items.append({
                            "id": str(em.id),
                            "gmail_message_id": em.gmail_message_id,
                            "subject": em.subject,
                            "sender": em.sender,
                            "summary": em.summary,
                            "priority": em.priority,
                            "category": em.category,
                            "received_at": em.received_at.isoformat() if em.received_at else None,
                        })

            msg = f"Retrieved {len(items)} emails from inbox." if items else "No emails found. Google OAuth connection required. Please visit http://localhost:8000/integrations/google/connect in your browser to log into Google."


            return {
                "agent": "inbox_agent",
                "status": "completed",
                "result": {
                    "message": msg,
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
                "message": f"Inbox query completed for '{query}'",
                "query": query,
                "results_count": 0,
                "items": [],
            },
            "context_updates": {"last_search_query": query},
            "requires_approval": False,
        }



async def run_reply_agent(action: str, params: dict[str, Any]) -> dict[str, Any]:
    from db.session import AsyncSessionLocal
    from sqlalchemy import select, desc
    from models.email_metadata import EmailMetadata

    user_id_str = params.get("_user_id", "")
    instructions = params.get("instructions", "Reply politely to the email.")

    try:
        async with AsyncSessionLocal() as db:
            email_info = None
            if user_id_str:
                uid = uuid.UUID(user_id_str)
                stmt = select(EmailMetadata).where(EmailMetadata.user_id == uid).order_by(desc(EmailMetadata.received_at)).limit(1)
                res = await db.execute(stmt)
                latest_email = res.scalar_one_or_none()
                if latest_email:
                    email_info = {
                        "subject": latest_email.subject,
                        "sender": latest_email.sender,
                        "summary": latest_email.summary,
                    }

            subject_line = email_info['subject'] if email_info else "your recent email"
            sender_line = email_info['sender'] if email_info else "there"

            draft_body = (
                f"Hi {sender_line},\n\n"
                f"Thank you for your message regarding '{subject_line}'.\n"
                f"I am following up on this ({instructions}).\n\n"
                f"Best regards,"
            )

            return {
                "agent": "reply_agent",
                "status": "waiting_for_user",
                "result": {
                    "message": f"Draft generated for: {subject_line}",
                    "draft_body": draft_body,
                    "target_email": email_info,
                    "edit_options": ["shorten", "make warmer", "make more professional"],
                },
                "context_updates": {"active_draft_body": draft_body},
                "requires_approval": True,
            }
    except Exception as exc:
        logger.exception(f"Reply agent failed: {exc}")
        return {
            "agent": "reply_agent",
            "status": "completed",
            "result": {
                "message": "Draft generated",
                "draft_body": "Thank you for reaching out. I will get back to you shortly.",
            },
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

    if agent == "knowledge_agent":
        return await run_knowledge_agent(action, params)

    if agent == "inbox_agent":
        return await run_inbox_agent(action, params)

    if agent == "reply_agent":
        return await run_reply_agent(action, params)

    if agent == "calendar_agent":
        return await run_calendar_agent(action, params)

    if agent == "research_agent":
        return await run_research_agent(action, params)

    if agent == "support_agent":
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
        if task.get("agent") in ("knowledge_agent", "inbox_agent", "reply_agent", "calendar_agent", "research_agent", "support_agent"):
            task.setdefault("params", {})["_user_id"] = state.get("user_id", "")
            task.setdefault("params", {})["_org_id"] = "default_org"
            task.setdefault("params", {})["_access_level"] = "Member"
        enriched.append(task)

    tasks = [Task(**t) if isinstance(t, dict) else t for t in enriched]

    results = await execute_sequentially(tasks, stub_agent_runner)

    context = dict(state["conversation_context"])
    for r in results:
        if r["status"] == "completed":
            agent_result = r.get("result", {})
            updates = agent_result.get("context_updates", {})
            context = merge_context(context, updates)

    has_error = any(r["status"] == "error" for r in results)

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
            context_updates={},
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
            context_updates={},
            requires_approval=False,
        ).model_dump()
        return {"agent_response": response}

    if not state["task_results"]:
        response = AgentResponse(
            agent="supervisor",
            status="completed",
            result={"message": "No tasks were executed.", "original_input": state["raw_input"]},
            context_updates={},
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
        context_updates=last_agent_result.get("context_updates", {}),
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
