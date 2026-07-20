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


async def stub_agent_runner(agent: str, action: str, params: dict[str, Any]) -> dict[str, Any]:
    logger.info(f"Stub agent runner: {agent}/{action} with params={params}")

    if agent == "knowledge_agent":
        return await run_knowledge_agent(action, params)

    if agent == "inbox_agent":
        return {
            "agent": "inbox_agent",
            "status": "completed",
            "result": {
                "message": f"Stub inbox response for action '{action}'",
                "query": params.get("query", ""),
                "results_count": 3,
                "items": [
                    {"id": "email_1", "subject": "Q4 Board Meeting", "sender": "board@company.com", "priority": "High"},
                    {"id": "email_2", "subject": "Invoice #1042 Due", "sender": "finance@vendor.com", "priority": "High"},
                    {"id": "email_3", "subject": "Team standup notes", "sender": "alice@company.com", "priority": "Medium"},
                ],
            },
            "context_updates": {"last_search_query": params.get("query", "")},
            "requires_approval": False,
        }

    if agent == "reply_agent":
        return {
            "agent": "reply_agent",
            "status": "waiting_for_user",
            "result": {
                "message": f"Draft generated for action '{action}'",
                "draft_body": "Thank you for your email. I'd be happy to help with that.",
                "edit_options": ["shorten", "make warmer", "make more professional"],
            },
            "context_updates": {"active_draft_id": "draft_stub_1"},
            "requires_approval": False,
        }

    if agent == "calendar_agent":
        return {
            "agent": "calendar_agent",
            "status": "waiting_for_user",
            "result": {
                "message": "Meeting preview generated",
                "proposed_slots": [
                    {"date": "2026-07-20", "time": "14:00", "duration": "60 min"},
                    {"date": "2026-07-21", "time": "10:00", "duration": "60 min"},
                ],
                "attendees": params.get("participants", ["user@example.com"]),
            },
            "context_updates": {},
            "requires_approval": True,
        }

    if agent == "research_agent":
        return {
            "agent": "research_agent",
            "status": "completed",
            "result": {
                "message": f"Research completed for '{params.get('company', '')}'",
                "executive_summary": f"{params.get('company', 'The company')} is a technology company...",
                "swot": {"strengths": ["Strong product"], "weaknesses": [], "opportunities": [], "threats": []},
            },
            "context_updates": {},
            "requires_approval": False,
        }

    if agent == "support_agent":
        return {
            "agent": "support_agent",
            "status": "completed",
            "result": {
                "message": f"Support answer for '{params.get('question', '')}'",
                "answer": "You can search emails by saying 'show me emails from' or typing it in the command bar.",
            },
            "context_updates": {},
            "requires_approval": False,
        }

    return {
        "agent": agent,
        "status": "completed",
        "result": {"message": f"Stub response for {agent}/{action}"},
        "context_updates": {},
        "requires_approval": False,
    }


async def execute_tasks_node(state: SupervisorState) -> dict[str, Any]:
    raw_tasks = state["task_queue"]
    enriched = []
    for t in raw_tasks:
        task = t if isinstance(t, dict) else {"agent": t.agent, "action": t.action, "params": t.params}
        if task.get("agent") in ("knowledge_agent", "inbox_agent", "reply_agent", "calendar_agent"):
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
