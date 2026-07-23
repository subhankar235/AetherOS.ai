import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from core.exceptions import ApprovalRequiredError, NotFoundError
from models.draft import Draft
from models.email_metadata import EmailMetadata
from models.user import User, UserRole
from models.agent_log import AgentLog
from agents.reply_agent.drafter import generate_draft, DraftOutput
from agents.reply_agent.editor import edit_draft
from agents.reply_agent.sender import prepare_send, execute_send


# ==========================================
# 1. Draft Generation & Gaps Detection Tests
# ==========================================

@pytest.mark.asyncio
@patch("agents.reply_agent.drafter.fetch_message", new_callable=AsyncMock)
@patch("agents.reply_agent.drafter.ChatOpenAI")
async def test_generate_draft_with_gaps_flag(mock_chat_class, mock_fetch):
    user_id = uuid.uuid4()
    email_id = uuid.uuid4()

    mock_db = AsyncMock()
    mock_db.add = MagicMock()

    # Mock email metadata lookup
    email_meta = EmailMetadata(
        id=email_id,
        user_id=user_id,
        gmail_message_id="msg_reply_123",
        subject="Question about Refund Policy",
        sender="customer@company.com",
    )
    mock_execute_result = MagicMock()
    mock_execute_result.scalar_one_or_none.return_value = email_meta
    mock_db.execute.return_value = mock_execute_result

    # Mock fetch_message
    mock_fetch.return_value = {
        "id": "msg_reply_123",
        "threadId": "thread_reply_123",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Question about Refund Policy"},
                {"name": "From", "value": "customer@company.com"},
            ],
            "mimeType": "text/plain",
            "body": {"data": "SGkLCB3aGF0IGlzIHlvdXIgcmVmdW5kIHdpbmRvdz8="},
        },
    }

    # Mock ChatOpenAI structured output
    mock_llm = MagicMock()
    mock_structured_llm = AsyncMock()
    mock_structured_llm.ainvoke.return_value = DraftOutput(
        body="Thank you for reaching out regarding our refund policy.",
        has_gaps=True,
        gap_notes=["I don't have our current refund window — please confirm"],
    )
    mock_llm.with_structured_output.return_value = mock_structured_llm
    mock_chat_class.return_value = mock_llm

    draft = await generate_draft(user_id=user_id, email_id=email_id, db=mock_db, instructions="reply politely")

    assert draft is not None
    assert "Thank you for reaching out" in draft.current_body
    assert "Gaps detected" in draft.current_body
    assert len(draft.version_history) == 1
    assert draft.version_history[0]["has_gaps"] is True
    assert getattr(draft, "has_gaps", False) is True
    assert getattr(draft, "gap_notes", []) == ["I don't have our current refund window — please confirm"]


@pytest.mark.asyncio
@patch("agents.knowledge_agent.retriever.query_knowledge", new_callable=AsyncMock)
@patch("agents.reply_agent.drafter.fetch_message", new_callable=AsyncMock)
@patch("agents.reply_agent.drafter.ChatOpenAI")
async def test_generate_draft_grounding_and_kb_query(mock_chat_class, mock_fetch, mock_query_kb):
    user_id = uuid.uuid4()
    email_id = uuid.uuid4()

    mock_db = AsyncMock()
    mock_db.add = MagicMock()

    email_meta = EmailMetadata(
        id=email_id,
        user_id=user_id,
        gmail_message_id="msg_kb_999",
        subject="Pricing Inquiry for Enterprise Tier",
        sender="enterprise@client.com",
    )
    mock_execute_result = MagicMock()
    mock_execute_result.scalar_one_or_none.return_value = email_meta
    mock_db.execute.return_value = mock_execute_result

    mock_fetch.return_value = {
        "id": "msg_kb_999",
        "threadId": "thread_kb_999",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Pricing Inquiry for Enterprise Tier"},
                {"name": "From", "value": "enterprise@client.com"},
            ],
            "mimeType": "text/plain",
            "body": {"data": "SGkgd2hhdCBpcyB0aGUgZW50ZXJwcmlzZSBwcmljaW5nPw=="},
        },
    }

    mock_query_kb.return_value = {
        "agent": "knowledge_agent",
        "status": "completed",
        "result": {"answer": "Enterprise tier costs $500/mo billed annually."},
    }

    mock_llm = MagicMock()
    mock_structured_llm = AsyncMock()
    mock_structured_llm.ainvoke.return_value = DraftOutput(
        body="Hi Enterprise Client, our Enterprise tier is $500/mo billed annually.",
        has_gaps=False,
        gap_notes=[],
    )
    mock_llm.with_structured_output.return_value = mock_structured_llm
    mock_chat_class.return_value = mock_llm

    draft = await generate_draft(user_id=user_id, email_id=email_id, db=mock_db)

    assert draft is not None
    assert "Enterprise tier is $500/mo" in draft.current_body
    assert getattr(draft, "has_gaps", True) is False
    assert getattr(draft, "gap_notes", ["dummy"]) == []
    mock_query_kb.assert_called_once()



# ==========================================
# 2. Rewrite-In-Place Editor Tests
# ==========================================

@pytest.mark.asyncio
@patch("agents.reply_agent.editor.ChatOpenAI")
async def test_edit_draft_preserves_version_history(mock_chat_class):
    user_id = uuid.uuid4()
    draft_id = uuid.uuid4()

    mock_db = AsyncMock()

    initial_version = {
        "version": 1,
        "body": "Thank you for reaching out. We will process your request shortly.",
        "timestamp": "2026-07-22T12:00:00Z",
        "source": "ai_generated",
    }

    draft = Draft(
        id=draft_id,
        user_id=user_id,
        current_body="Thank you for reaching out. We will process your request shortly. (User added: Best, Bob)",
        version_history=[initial_version],
        status="drafting",
    )

    mock_execute_result = MagicMock()
    mock_execute_result.scalar_one_or_none.return_value = draft
    mock_db.execute.return_value = mock_execute_result

    mock_llm = AsyncMock()
    mock_chat_class.return_value = mock_llm
    mock_llm.ainvoke.return_value = MagicMock(content="Thanks! We'll process your request shortly. Best, Bob")

    updated_draft = await edit_draft(draft_id=draft_id, user_id=user_id, instructions="shorten it", db=mock_db)

    assert updated_draft.current_body == "Thanks! We'll process your request shortly. Best, Bob"
    assert len(updated_draft.version_history) == 2
    assert updated_draft.version_history[1]["version"] == 2
    assert updated_draft.version_history[1]["instructions"] == "shorten it"


# ==========================================
# 3. Sender & Approval Gate Lifecycle Tests (Exit Criteria)
# ==========================================

@pytest.mark.asyncio
@patch("agents.reply_agent.sender.create_approval_request", new_callable=AsyncMock)
async def test_prepare_send_creates_approval(mock_create_approval):
    user_id = uuid.uuid4()
    draft_id = uuid.uuid4()
    email_id = uuid.uuid4()
    approval_id = uuid.uuid4()

    mock_db = AsyncMock()

    draft = Draft(
        id=draft_id,
        user_id=user_id,
        email_id=email_id,
        current_body="Final draft body.",
        status="drafting",
    )
    email_meta = EmailMetadata(
        id=email_id,
        user_id=user_id,
        sender="sarah@acme.com",
        subject="Renewal details",
        gmail_message_id="msg_sarah_123",
    )

    def mock_db_execute(stmt):
        mock_res = MagicMock()
        # First call is for Draft, second is for EmailMetadata
        if "drafts" in str(stmt).lower():
            mock_res.scalar_one_or_none.return_value = draft
        else:
            mock_res.scalar_one_or_none.return_value = email_meta
        return mock_res

    mock_db.execute.side_effect = mock_db_execute
    mock_create_approval.return_value = approval_id

    result = await prepare_send(draft_id=draft_id, user_id=user_id, db=mock_db)

    assert result["requires_approval"] is True
    assert result["approval_id"] == str(approval_id)
    assert result["confirmation"]["recipient"] == "sarah@acme.com"


@pytest.mark.asyncio
@patch("agents.reply_agent.sender.log_agent_action", new_callable=AsyncMock)
@patch("agents.reply_agent.sender.send_message", new_callable=AsyncMock)
@patch("agents.reply_agent.sender.require_valid_approval", new_callable=AsyncMock)
async def test_execute_send_requires_approval_and_logs(mock_require_approval, mock_send_msg, mock_log_audit):
    user_id = uuid.uuid4()
    draft_id = uuid.uuid4()
    email_id = uuid.uuid4()
    approval_id = uuid.uuid4()

    mock_user = User(id=user_id, clerk_user_id="clerk_123", email="user@test.com", role=UserRole.MEMBER)

    mock_db = AsyncMock()

    draft = Draft(
        id=draft_id,
        user_id=user_id,
        email_id=email_id,
        current_body="Final draft body to send.",
        status="drafting",
    )
    email_meta = EmailMetadata(
        id=email_id,
        user_id=user_id,
        sender="sarah@acme.com",
        subject="Renewal details",
        gmail_message_id="msg_sarah_123",
    )

    def mock_db_execute(stmt):
        mock_res = MagicMock()
        if "drafts" in str(stmt).lower():
            mock_res.scalar_one_or_none.return_value = draft
        else:
            mock_res.scalar_one_or_none.return_value = email_meta
        return mock_res

    mock_db.execute.side_effect = mock_db_execute

    # Case 1: require_valid_approval raises ApprovalRequiredError -> send fails
    mock_require_approval.side_effect = ApprovalRequiredError("Approval required")
    with pytest.raises(ApprovalRequiredError):
        await execute_send(draft_id=draft_id, approval_id=approval_id, user=mock_user, db=mock_db)

    # Case 2: Approval passes -> email sends and audit is logged
    mock_require_approval.side_effect = None
    mock_send_msg.return_value = {"id": "gmail_sent_999", "threadId": "thread_999"}

    send_result = await execute_send(draft_id=draft_id, approval_id=approval_id, user=mock_user, db=mock_db)

    assert send_result["status"] == "sent"
    assert send_result["gmail_message_id"] == "gmail_sent_999"
    assert draft.status == "sent"
    mock_log_audit.assert_called_once()
