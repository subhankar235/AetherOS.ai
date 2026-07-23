import pytest
from unittest.mock import patch, MagicMock
from core.llm_factory import get_provider_candidates, invoke_llm_with_fallback

def test_get_provider_candidates(monkeypatch):
    from core.config import settings
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "sk-or-v1-testkey")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "gsk_testgroqkey")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "AIza_testgeminikey")
    monkeypatch.setattr(settings, "LLM_FALLBACK_ORDER", "openrouter,groq,gemini")

    candidates = get_provider_candidates(is_classifier=True)
    assert len(candidates) == 3
    assert candidates[0]["name"] == "openrouter"
    assert candidates[1]["name"] == "groq"
    assert candidates[2]["name"] == "gemini"


def test_invoke_llm_with_fallback_success_on_second_candidate(monkeypatch):
    from core.config import settings
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "sk-or-v1-invalidkey")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "gsk_validkey")
    monkeypatch.setattr(settings, "LLM_FALLBACK_ORDER", "openrouter,groq")

    # Mock ChatOpenAI so first invocation raises Exception and second succeeds
    mock_llm_1 = MagicMock()
    mock_llm_1.bind_tools.return_value.invoke.side_effect = Exception("OpenRouter key credit exhausted (402)")

    mock_llm_2 = MagicMock()
    mock_response = MagicMock()
    mock_response.tool_calls = [{"name": "inbox_agent_search", "args": {"query": "unread emails"}}]
    mock_llm_2.bind_tools.return_value.invoke.return_value = mock_response

    with patch("core.llm_factory.ChatOpenAI", side_effect=[mock_llm_1, mock_llm_2]):
        messages = [{"role": "user", "content": "find unread emails"}]
        tools = [{"type": "function", "function": {"name": "inbox_agent_search", "description": "search inbox"}}]

        res, provider_used = invoke_llm_with_fallback(messages=messages, tools=tools)

        assert provider_used == "groq"
        assert res.tool_calls[0]["name"] == "inbox_agent_search"
