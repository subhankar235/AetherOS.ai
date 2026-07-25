import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from agents.supervisor.graph import SupervisorGraph
from voice.voice_session import VoiceSessionCoordinator
from voice.conversational_rewrite import rewrite


@pytest.mark.asyncio
async def test_identity_who_are_you():
    graph = SupervisorGraph()
    response = await graph.run(
        user_id="test_user_1",
        session_id="session_1",
        raw_input="Who are you?",
    )
    assert response["agent"] == "support_agent"
    assert response["status"] == "completed"
    answer = response["result"].get("answer") or response["result"].get("message") or ""
    assert "AetherOS.ai" in answer


@pytest.mark.asyncio
async def test_identity_what_is_your_name():
    graph = SupervisorGraph()
    response = await graph.run(
        user_id="test_user_0",
        session_id="session_0",
        raw_input="What is your name?",
    )
    assert response["agent"] == "support_agent"
    assert response["status"] == "completed"
    answer = response["result"].get("answer") or response["result"].get("message") or ""
    assert "AetherOS.ai" in answer


@pytest.mark.asyncio
async def test_identity_what_can_you_do():
    graph = SupervisorGraph()
    response = await graph.run(
        user_id="test_user_2",
        session_id="session_2",
        raw_input="What can you do?",
    )
    assert response["agent"] == "support_agent"
    assert response["status"] == "completed"
    answer = response["result"].get("answer") or response["result"].get("message") or ""
    assert "AetherOS.ai" in answer or "inbox" in answer.lower() or "schedule" in answer.lower()


@pytest.mark.asyncio
async def test_identity_how_are_you():
    graph = SupervisorGraph()
    response = await graph.run(
        user_id="test_user_3",
        session_id="session_3",
        raw_input="How are you?",
    )
    assert response["agent"] == "support_agent"
    assert response["status"] == "completed"
    answer = response["result"].get("answer") or response["result"].get("message") or ""
    assert len(answer) > 10


@pytest.mark.asyncio
async def test_identity_how_can_you_help_me():
    graph = SupervisorGraph()
    response = await graph.run(
        user_id="test_user_4",
        session_id="session_4",
        raw_input="How can you help me?",
    )
    assert response["agent"] == "support_agent"
    assert response["status"] == "completed"
    answer = response["result"].get("answer") or response["result"].get("message") or ""
    assert "AetherOS.ai" in answer or "help" in answer.lower() or "inbox" in answer.lower()


@pytest.mark.asyncio
async def test_identity_what_features_do_you_have():
    graph = SupervisorGraph()
    response = await graph.run(
        user_id="test_user_5",
        session_id="session_5",
        raw_input="What features do you have?",
    )
    assert response["agent"] == "support_agent"
    assert response["status"] == "completed"
    answer = response["result"].get("answer") or response["result"].get("message") or ""
    assert "AetherOS.ai" in answer or "email" in answer.lower() or "calendar" in answer.lower()


@pytest.mark.asyncio
async def test_voice_session_coordinator_turn():
    mock_stt = MagicMock()
    mock_stt.transcribe_stream.side_effect = lambda stream: _async_iter([{"type": "final", "text": "Who are you?"}])

    mock_tts = MagicMock()
    mock_tts.generate_speech_stream.side_effect = lambda text, voice_id: _async_iter([b"audio_chunk_1", b"audio_chunk_2"])

    coordinator = VoiceSessionCoordinator(stt_client=mock_stt, tts_client=mock_tts)

    mock_user = MagicMock()
    mock_user.id = "user_999"
    mock_user.email = "test@example.com"
    mock_user.voice_history_opt_in = False
    mock_user.voice_profile_id = None

    async def mock_audio_input():
        yield b"input_mic_audio"

    chunks = []
    async for chunk in coordinator.process_voice_turn(mock_user, mock_audio_input(), session_id="voice_sess_1"):
        chunks.append(chunk)

    assert len(chunks) == 2
    assert chunks == [b"audio_chunk_1", b"audio_chunk_2"]


async def _async_iter(items):
    for item in items:
        yield item
