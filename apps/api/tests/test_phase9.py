import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock

from core.exceptions import ApprovalRequiredError
from schemas.agent_response_schema import AgentResponse
from services.approval.approval_gate import (
    create_approval_request,
    approve,
    reject,
    require_valid_approval,
)
from services.audit.audit_logger import (
    log_agent_action,
    _redact_payload,
    SECRET_FIELD_NAMES,
)
from models.agent_log import AgentLog


# ==========================================
# 1. Agent Response Schema Tests
# ==========================================

def test_agent_response_schema_validation():
    response = AgentResponse(
        agent="inbox_agent",
        status="completed",
        result={"summary": "Synced 5 emails"},
        context_updates={"unread_count": 5},
        requires_approval=False,
    )
    assert response.agent == "inbox_agent"
    assert response.status == "completed"
    assert response.requires_approval is False

    with pytest.raises(Exception):
        # Invalid status should fail Pydantic validation
        AgentResponse(
            agent="inbox_agent",
            status="invalid_status",  # type: ignore
            result={},
        )


# ==========================================
# 2. Approval Gate Flow Tests (Phase 9 Exit Criteria)
# ==========================================

@pytest.mark.asyncio
async def test_approval_gate_lifecycle():
    user_id = uuid.uuid4()
    artifact_id = "draft_123"
    action_type = "send_email"
    
    # Mock DB Session
    mock_db = AsyncMock()
    stored_log = None
    def mock_add(instance):
        nonlocal stored_log
        stored_log = instance
    mock_db.add = MagicMock(side_effect=mock_add)

    # Step 1: Create approval request -> status="pending_approval"
    approval_id = await create_approval_request(
        db=mock_db,
        user_id=user_id,
        action_type=action_type,
        artifact_id=artifact_id,
        payload={"recipient": "boss@company.com", "subject": "Quarterly Report"},
        agent_name="reply_agent",
    )
    assert approval_id is not None
    assert stored_log.status == "pending_approval"
    assert stored_log.requires_approval is True

    # Step 2: Attempt to execute action without approving -> expect ApprovalRequiredError
    mock_execute_result = MagicMock()
    mock_execute_result.scalar_one_or_none.return_value = stored_log
    mock_db.execute.return_value = mock_execute_result

    with pytest.raises(ApprovalRequiredError) as exc_info:
        await require_valid_approval(db=mock_db, approval_id=approval_id, artifact_id=artifact_id)
    assert "expected 'approved'" in str(exc_info.value)

    # Step 3: Approve request -> status="approved"
    success = await approve(db=mock_db, approval_id=approval_id, approved_by="user@example.com")
    assert success is True
    assert stored_log.status == "approved"
    assert stored_log.approved_by == "user@example.com"
    assert stored_log.approved_at is not None

    # Step 4: Re-attempt action -> successfully pass approval check
    await require_valid_approval(db=mock_db, approval_id=approval_id, artifact_id=artifact_id)


@pytest.mark.asyncio
async def test_approval_gate_rejection():
    user_id = uuid.uuid4()
    mock_db = AsyncMock()
    
    stored_log = AgentLog(
        id=uuid.uuid4(),
        user_id=user_id,
        agent_name="reply_agent",
        action_type="send_email",
        status="pending_approval",
    )
    mock_execute_result = MagicMock()
    mock_execute_result.scalar_one_or_none.return_value = stored_log
    mock_db.execute.return_value = mock_execute_result

    success = await reject(db=mock_db, approval_id=stored_log.id, reason="User cancelled draft")
    assert success is True
    assert stored_log.status == "rejected"
    assert stored_log.output_payload == {"rejection_reason": "User cancelled draft"}


# ==========================================
# 3. Audit Logger & Secret Redaction Tests
# ==========================================

def test_audit_logger_redaction():
    sensitive_payload = {
        "user_email": "john@example.com",
        "api_key": "sk-proj-1234567890abcdef",
        "secret": "topsecretpassword",
        "nested": {
            "token": "bearer-token-xyz1234567890",
            "safe_field": "hello world",
        },
        "items": [
            {"client_secret": "GOCSPX-secret12345"},
            {"public_info": "ok"},
        ],
    }

    redacted = _redact_payload(sensitive_payload)

    assert redacted["user_email"] == "john@example.com"
    assert redacted["api_key"] == "***REDACTED***"
    assert redacted["secret"] == "***REDACTED***"
    assert redacted["nested"]["token"] == "***REDACTED***"
    assert redacted["nested"]["safe_field"] == "hello world"
    assert redacted["items"][0]["client_secret"] == "***REDACTED***"
    assert redacted["items"][1]["public_info"] == "ok"


@pytest.mark.asyncio
async def test_log_agent_action_persists_redacted_log():
    mock_db = AsyncMock()
    stored_log = None
    def mock_add(instance):
        nonlocal stored_log
        stored_log = instance
    mock_db.add = MagicMock(side_effect=mock_add)

    user_id = uuid.uuid4()
    await log_agent_action(
        db=mock_db,
        user_id=user_id,
        agent_name="research_agent",
        action_type="web_search",
        input_payload={"query": "Aether AI", "openai_api_key": "sk-1234567890abcdef"},
        output_payload={"results": ["res1"], "secret": "shhh"},
        status="completed",
    )

    assert stored_log is not None
    assert stored_log.agent_name == "research_agent"
    assert stored_log.input_payload["openai_api_key"] == "***REDACTED***"
    assert stored_log.output_payload["secret"] == "***REDACTED***"
    assert stored_log.status == "completed"
