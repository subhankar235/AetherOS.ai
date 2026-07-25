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
async def test_general_conversation_tell_joke():
    graph = SupervisorGraph()
    response = await graph.run(
        user_id="test_user_6",
        session_id="session_6",
        raw_input="Tell me a joke.",
    )
    assert response["agent"] == "support_agent"
    assert response["status"] == "completed"
    answer = response["result"].get("answer") or response["result"].get("message") or ""
    assert len(answer) > 10


@pytest.mark.asyncio
async def test_general_conversation_explain_oauth():
    graph = SupervisorGraph()
    response = await graph.run(
        user_id="test_user_7",
        session_id="session_7",
        raw_input="Explain OAuth.",
    )
    assert response["agent"] == "support_agent"
    assert response["status"] == "completed"
    answer = response["result"].get("answer") or response["result"].get("message") or ""
    assert len(answer) > 10


@pytest.mark.asyncio
async def test_task_execution_workflow_multi_step_summary():
    graph = SupervisorGraph()
    mock_classification = {
        "intent": "multi_step",
        "tasks": [
            {"agent": "reply_agent", "action": "draft", "params": {"instructions": "reply to John", "target_email": "John"}},
            {"agent": "calendar_agent", "action": "schedule", "params": {"title": "Sync with John", "time": "tomorrow at 3 PM"}},
        ],
        "clarification_text": None,
    }

    with patch("agents.supervisor.graph.classify_intent", new_callable=AsyncMock) as mock_classify:
        mock_classify.return_value = mock_classification

        response = await graph.run(
            user_id="test_user_workflow",
            session_id="session_wf",
            raw_input="Reply to John's email and schedule a meeting.",
        )
        assert response["status"] in ("completed", "previewed", "drafting")
        rewritten = rewrite(response)
        assert len(rewritten) > 10


@pytest.mark.asyncio
async def test_concise_completion_summary_default():
    # Verify default output is concise and doesn't dump full text
    sample_response = {
        "agent": "reply_agent",
        "status": "completed",
        "result": {
            "draft_id": "draft_123",
            "draft_body": "This is a very long draft email body containing extensive multi-paragraph details about the meeting...",
            "target_email": {"sender": "John Doe"},
        },
        "requires_approval": False,
    }
    rewritten = rewrite(sample_response)
    assert rewritten == "Draft created for John Doe."
    assert "very long draft email body" not in rewritten


@pytest.mark.asyncio
async def test_read_draft_on_explicit_request():
    graph = SupervisorGraph()
    response = await graph.run(
        user_id="test_user_read",
        session_id="session_read",
        raw_input="Show me the draft.",
    )
    assert response["agent"] == "reply_agent"
    assert response["status"] == "completed"
    answer = response["result"].get("answer", "")
    assert "draft" in answer.lower()


@pytest.mark.asyncio
async def test_continuous_multi_turn_conversation_flow():
    graph = SupervisorGraph()
    session_id = "multi_turn_session_100"
    user_id = "test_user_multi_turn"

    # Turn 1: "Reply to John's email."
    mock_class_1 = {
        "intent": "single",
        "tasks": [{"agent": "reply_agent", "action": "draft", "params": {"instructions": "reply to John", "target_email": "John"}}],
        "clarification_text": None,
    }
    with patch("agents.supervisor.graph.classify_intent", new_callable=AsyncMock) as mock_classify:
        mock_classify.return_value = mock_class_1
        turn_1_res = await graph.run(user_id=user_id, session_id=session_id, raw_input="Reply to John's email.")
        t1_spoken = rewrite(turn_1_res)
        assert len(t1_spoken) > 5

    # Turn 2: "Don't read it."
    mock_class_2 = {
        "intent": "single",
        "tasks": [{"agent": "support_agent", "action": "help", "params": {"question": "Don't read it."}}],
        "clarification_text": None,
    }
    with patch("agents.supervisor.graph.classify_intent", new_callable=AsyncMock) as mock_classify:
        mock_classify.return_value = mock_class_2
        turn_2_res = await graph.run(user_id=user_id, session_id=session_id, raw_input="Don't read it.")
        t2_spoken = rewrite(turn_2_res)
        assert t2_spoken == "No problem."

    # Turn 3: "Now schedule a meeting with him." (Pronoun 'him' resolves to John from context)
    mock_class_3 = {
        "intent": "single",
        "tasks": [{"agent": "calendar_agent", "action": "schedule", "params": {"raw_input": "schedule a meeting with him", "description": "meeting with him"}}],
        "clarification_text": None,
    }
    with patch("agents.supervisor.graph.classify_intent", new_callable=AsyncMock) as mock_classify, \
         patch("agents.calendar_agent.extractor.extract_meeting_details", new_callable=AsyncMock) as mock_extract:
        mock_classify.return_value = mock_class_3
        from agents.calendar_agent.extractor import MeetingDetails
        mock_extract.return_value = MeetingDetails(title="Sync with John", duration_minutes=60, participants=["john@example.com"])
        turn_3_res = await graph.run(user_id=user_id, session_id=session_id, raw_input="Now schedule a meeting with him.")
        t3_spoken = rewrite(turn_3_res)
        assert len(t3_spoken) > 5


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


@pytest.mark.asyncio
async def test_voice_interruption_halts_speech_immediately():
    mock_stt = MagicMock()
    mock_stt.transcribe_stream.side_effect = lambda stream: _async_iter([{"type": "final", "text": "Who are you?"}])

    async def slow_tts_stream(text, voice_id):
        yield b"chunk_1"
        yield b"chunk_2"
        yield b"chunk_3"

    mock_tts = MagicMock()
    mock_tts.generate_speech_stream.side_effect = slow_tts_stream

    coordinator = VoiceSessionCoordinator(stt_client=mock_stt, tts_client=mock_tts)

    mock_user = MagicMock()
    mock_user.id = "user_interrupt"
    mock_user.email = "interrupt@example.com"
    mock_user.voice_history_opt_in = False
    mock_user.voice_profile_id = None

    async def mock_audio_input():
        yield b"audio_input"

    chunks = []
    async for chunk in coordinator.process_voice_turn(mock_user, mock_audio_input(), session_id="sess_interrupt"):
        chunks.append(chunk)
        if len(chunks) == 1:
            coordinator.interrupt()

    assert len(chunks) == 1
    assert chunks == [b"chunk_1"]


@pytest.mark.asyncio
async def test_voice_interruption_remembers_completed_task_context():
    graph = SupervisorGraph()
    session_id = "session_interrupted_context"
    user_id = "user_interrupted_context"

    # Step 1: User requests drafting reply to John
    mock_class_1 = {
        "intent": "single",
        "tasks": [{"agent": "reply_agent", "action": "draft", "params": {"instructions": "reply to John", "target_email": "John"}}],
        "clarification_text": None,
    }
    with patch("agents.supervisor.graph.classify_intent", new_callable=AsyncMock) as mock_classify:
        mock_classify.return_value = mock_class_1
        res1 = await graph.run(user_id=user_id, session_id=session_id, raw_input="Reply to John's email.")

    # Context remembers completed task and active recipient
    assert res1["context_updates"].get("active_recipient") is not None

    # Step 2: User interrupts ("No need to read it.")
    mock_class_2 = {
        "intent": "single",
        "tasks": [{"agent": "support_agent", "action": "help", "params": {"question": "No need to read it."}}],
        "clarification_text": None,
    }
    with patch("agents.supervisor.graph.classify_intent", new_callable=AsyncMock) as mock_classify:
        mock_classify.return_value = mock_class_2
        res2 = await graph.run(user_id=user_id, session_id=session_id, raw_input="No need to read it.")
        spoken = rewrite(res2)
        assert spoken == "No problem."


@pytest.mark.asyncio
async def test_vad_confidence_filtering_ignores_ambient_noise():
    import json
    from voice.stt_client import SpeechToTextClient
    client = SpeechToTextClient(api_key="mock_key")

    mock_ws = AsyncMock()
    # Mock WebSocket messages: 1 low-confidence noise transcript (0.2), 1 high-confidence speech transcript (0.95), 1 session_ended
    messages = [
        json.dumps({"message_type": "transcript", "text": "cough noise", "confidence": 0.2}),
        json.dumps({"message_type": "transcript", "text": "Schedule a meeting", "confidence": 0.95}),
        json.dumps({"message_type": "session_ended"}),
    ]

    async def mock_ws_iter():
        for msg in messages:
            yield msg

    mock_ws.__aiter__ = lambda self: mock_ws_iter()

    def mock_connect(*args, **kwargs):
        class MockWSContext:
            async def __aenter__(self):
                return mock_ws
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
        return MockWSContext()

    async def empty_audio_gen():
        return
        yield b""

    with patch("websockets.connect", side_effect=mock_connect):
        results = []
        async for update in client.transcribe_stream(empty_audio_gen()):
            results.append(update)

        assert len(results) == 1
        assert results[0]["type"] == "final"
        assert results[0]["confidence"] == 0.95


@pytest.mark.asyncio
async def test_voice_interruption_task_redirection():
    graph = SupervisorGraph()
    session_id = "session_redirect_task_99"
    user_id = "user_redirect_task_99"

    mock_class_1 = {
        "intent": "single",
        "tasks": [{"agent": "support_agent", "action": "help", "params": {"question": "Who are you?"}}],
        "clarification_text": None,
    }
    with patch("agents.supervisor.graph.classify_intent", new_callable=AsyncMock) as mock_classify:
        mock_classify.return_value = mock_class_1
        res1 = await graph.run(user_id=user_id, session_id=session_id, raw_input="Who are you?")

    assert res1["status"] == "completed"

    # User interrupts mid-way and redirects to a completely different task (schedule meeting with Sarah)
    mock_class_2 = {
        "intent": "single",
        "tasks": [{"agent": "calendar_agent", "action": "schedule", "params": {"raw_input": "schedule a meeting with Sarah tomorrow at 2 PM", "description": "meeting with Sarah"}}],
        "clarification_text": None,
    }
    with patch("agents.supervisor.graph.classify_intent", new_callable=AsyncMock) as mock_classify, \
         patch("agents.calendar_agent.extractor.extract_meeting_details", new_callable=AsyncMock) as mock_extract:
        mock_classify.return_value = mock_class_2
        from agents.calendar_agent.extractor import MeetingDetails
        mock_extract.return_value = MeetingDetails(title="Sync with Sarah", duration_minutes=60, participants=["sarah@example.com"])

        res2 = await graph.run(user_id=user_id, session_id=session_id, raw_input="Wait, schedule a meeting with Sarah tomorrow at 2 PM instead.")
        spoken = rewrite(res2)

        # Verified: Redirected task executes successfully and returns concise outcome summary
        assert res2["agent"] in ("calendar_agent", "Supervisor")
        assert "Sarah" in spoken or "Sync with Sarah" in spoken or "scheduled" in spoken.lower() or "meeting" in spoken.lower()


async def _async_iter(items):
    for item in items:
        yield item
    for item in items:
        yield item
