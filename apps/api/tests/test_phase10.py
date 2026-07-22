import pytest
from unittest.mock import AsyncMock, patch

from agents.supervisor.graph import SupervisorGraph, create_initial_state
from agents.supervisor.context_manager import resolve_reference, format_clarification
from agents.supervisor.task_decomposer import decompose, execute_sequentially, Task
from agents.supervisor.prompts import INJECTION_GUARDRAIL, SYSTEM_PROMPT


# ==========================================
# 1. Prompt Injection Guardrail Tests
# ==========================================

def test_prompt_injection_guardrail_present():
    assert "SECURITY: CONTENT BOUNDARY" in INJECTION_GUARDRAIL
    assert "DATA" in INJECTION_GUARDRAIL
    assert INJECTION_GUARDRAIL in SYSTEM_PROMPT


# ==========================================
# 2. Context & Coreference Resolution Tests
# ==========================================

@pytest.mark.asyncio
async def test_resolve_reference_missing_context():
    # Empty context + "reply to it" -> missing_context
    empty_context = {"active_email_id": None}
    ref_status, resolved = await resolve_reference("reply to it", empty_context)
    assert ref_status == "missing_context"
    assert resolved is None
    
    clarification = format_clarification("active_email_id")
    assert "don't have an email in context" in clarification


@pytest.mark.asyncio
async def test_resolve_reference_with_context():
    active_context = {"active_email_id": "msg_999"}
    ref_status, resolved = await resolve_reference("reply to it", active_context)
    assert ref_status == "resolved"
    assert resolved["resolved_value"] == "msg_999"


# ==========================================
# 3. Task Decomposer Tests
# ==========================================

def test_task_decomposition():
    parsed_tasks = [
        {"agent": "inbox_agent", "action": "search", "params": {"query": "unread"}},
        {"agent": "reply_agent", "action": "draft", "params": {"instructions": "reply to last"}},
    ]
    tasks = decompose("search unread and draft reply", parsed_tasks)
    assert len(tasks) == 2
    assert tasks[0].agent == "inbox_agent"
    assert tasks[1].agent == "reply_agent"


@pytest.mark.asyncio
async def test_task_sequential_execution_halt_on_error():
    tasks = [
        Task(agent="inbox_agent", action="search", params={}),
        Task(agent="reply_agent", action="draft", params={}, depends_on="inbox_agent"),
    ]
    
    async def failing_stub_runner(agent, action, params):
        if agent == "inbox_agent":
            raise RuntimeError("Inbox service unavailable")
        return {"agent": agent, "status": "completed"}

    results = await execute_sequentially(tasks, failing_stub_runner)
    assert len(results) == 1
    assert results[0]["status"] == "error"
    assert "Inbox service unavailable" in results[0]["error"]


# ==========================================
# 4. Supervisor Graph End-to-End Tests (Phase 10 Exit Criteria)
# ==========================================

@pytest.mark.asyncio
async def test_supervisor_single_intent():
    graph = SupervisorGraph()
    
    mock_classification = {
        "intent": "single",
        "tasks": [{"agent": "inbox_agent", "action": "search", "params": {"query": "high priority"}}],
        "clarification_text": None,
    }

    with patch("agents.supervisor.graph.classify_intent", new_callable=AsyncMock) as mock_classify:
        mock_classify.return_value = mock_classification
        
        response = await graph.run(
            user_id="user_123",
            session_id="sess_abc",
            raw_input="read me the high priority ones",
        )

    assert response["agent"] == "inbox_agent"
    assert response["status"] == "completed"
    assert response["result"]["results_count"] == 3
    assert len(response["result"]["items"]) == 3


@pytest.mark.asyncio
async def test_supervisor_multi_step_intent():
    graph = SupervisorGraph()

    mock_classification = {
        "intent": "multi_step",
        "tasks": [
            {"agent": "inbox_agent", "action": "search", "params": {"query": "board meeting"}},
            {"agent": "reply_agent", "action": "draft", "params": {"instructions": "say I will attend"}},
        ],
        "clarification_text": None,
    }

    with patch("agents.supervisor.graph.classify_intent", new_callable=AsyncMock) as mock_classify:
        mock_classify.return_value = mock_classification

        response = await graph.run(
            user_id="user_123",
            session_id="sess_abc",
            raw_input="find board meeting email and draft a reply saying I will attend",
        )

    assert response["agent"] == "reply_agent"
    assert response["status"] == "waiting_for_user"
    assert "active_draft_id" in response["context_updates"]


@pytest.mark.asyncio
async def test_supervisor_ambiguous_empty_context_clarification():
    graph = SupervisorGraph()

    mock_classification = {
        "intent": "single",
        "tasks": [{"agent": "reply_agent", "action": "draft", "params": {"instructions": "reply to it"}}],
        "clarification_text": None,
    }

    with patch("agents.supervisor.graph.classify_intent", new_callable=AsyncMock) as mock_classify:
        mock_classify.return_value = mock_classification

        # Empty context with "reply to it" -> triggers clarification
        response = await graph.run(
            user_id="user_123",
            session_id="sess_abc",
            raw_input="reply to it",
            conversation_context={"active_email_id": None},
        )

    assert response["status"] == "clarification_needed"
    assert "don't have an email in context" in response["result"]["clarification"]
