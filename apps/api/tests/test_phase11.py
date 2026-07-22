import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agents.inbox_agent.auto_pipeline import (
    process_new_email,
    _strip_signatures_and_quotes,
    EmailClassification,
)
from agents.inbox_agent.search import build_gmail_query, natural_language_search
from agents.inbox_agent.reader import read_email, summarize_thread, _hierarchical_summarize
from models.email_metadata import EmailMetadata
from models.thread import Thread


# ==========================================
# 1. Auto Pipeline & Idempotency Tests
# ==========================================

def test_strip_signatures_and_quotes():
    body_with_sig = (
        "Hi John,\n\nPlease see attached report.\n\n"
        "--\nBest regards,\nAlice Smith\nCEO Acme Corp"
    )
    stripped = _strip_signatures_and_quotes(body_with_sig)
    assert "Please see attached report." in stripped
    assert "Best regards" not in stripped


@pytest.mark.asyncio
async def test_auto_pipeline_idempotency():
    user_id = uuid.uuid4()
    gmail_message_id = "msg_duplicate_123"

    mock_db = AsyncMock()
    
    # Mock existing record found in DB -> should skip and return None
    existing_record = EmailMetadata(
        id=uuid.uuid4(),
        user_id=user_id,
        gmail_message_id=gmail_message_id,
    )
    mock_execute_result = MagicMock()
    mock_execute_result.scalar_one_or_none.return_value = existing_record
    mock_db.execute.return_value = mock_execute_result

    result = await process_new_email(user_id=user_id, gmail_message_id=gmail_message_id, db=mock_db)
    assert result is None


@pytest.mark.asyncio
@patch("agents.inbox_agent.auto_pipeline._publish_dashboard_event", new_callable=AsyncMock)
@patch("agents.inbox_agent.auto_pipeline._classify_email", new_callable=AsyncMock)
@patch("agents.inbox_agent.auto_pipeline.fetch_message", new_callable=AsyncMock)
async def test_auto_pipeline_processing(mock_fetch, mock_classify, mock_publish):
    user_id = uuid.uuid4()
    gmail_msg_id = "msg_new_456"

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    
    # No existing record
    mock_execute_result = MagicMock()
    mock_execute_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_execute_result

    mock_fetch.return_value = {
        "id": gmail_msg_id,
        "threadId": "thread_abc",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Project Deadline Update"},
                {"name": "From", "value": "boss@company.com"},
                {"name": "Date", "value": "Wed, 22 Jul 2026 12:00:00 +0000"},
            ],
            "mimeType": "text/plain",
            "body": {"data": "SGkgdGVhbSwgdGhlIGRlYWRsaW5lIGlzIG1vdmVkIHRvIEZyaWRheS4="},
        },
    }

    mock_classify.return_value = EmailClassification(
        summary="Deadline moved to Friday.",
        priority="High",
        category="Internal",
        urgency=True,
        reply_required=False,
        suspicious_flag=False,
    )

    result = await process_new_email(user_id=user_id, gmail_message_id=gmail_msg_id, db=mock_db)

    assert result is not None
    assert result.gmail_message_id == gmail_msg_id
    assert result.priority == "High"
    assert result.category == "Internal"
    assert result.suspicious_flag is False
    mock_publish.assert_called_once()


# ==========================================
# 2. Natural Language Search Tests
# ==========================================

@pytest.mark.asyncio
async def test_build_gmail_query():
    mock_llm = MagicMock()
    mock_structured_llm = AsyncMock()
    mock_structured_llm.ainvoke.return_value = MagicMock(
        query="from:sundar after:2026/07/15 before:2026/07/22",
        explanation="Search emails from Sundar in the last week",
    )
    mock_llm.with_structured_output.return_value = mock_structured_llm

    result = await build_gmail_query("emails from Sundar last week", user_timezone="UTC", llm=mock_llm)
    assert result.query == "from:sundar after:2026/07/15 before:2026/07/22"


# ==========================================
# 3. Hierarchical Thread Summarization Tests
# ==========================================

@pytest.mark.asyncio
@patch("agents.inbox_agent.reader.ChatOpenAI")
async def test_hierarchical_thread_summarization(mock_chat_class):
    mock_llm = AsyncMock()
    mock_chat_class.return_value = mock_llm
    mock_llm.ainvoke.return_value = MagicMock(content="Chunk summary: discussed budget and timeline.")

    # Generate 40 synthetic messages (> 30 threshold)
    messages = [
        {
            "id": f"msg_{i}",
            "payload": {
                "headers": [{"name": "From", "value": f"user{i}@test.com"}],
                "mimeType": "text/plain",
                "body": {"data": "SGVsbG8gd29ybGQ="},
            },
        }
        for i in range(40)
    ]

    summary = await _hierarchical_summarize(messages)
    assert "[Chunk 1 Summary]" in summary
    assert "[Chunk 2 Summary]" in summary
    assert "[Chunk 3 Summary]" in summary
