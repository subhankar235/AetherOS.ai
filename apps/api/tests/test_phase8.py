import asyncio
import base64
import json
import os
import shutil
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import websockets
from core.exceptions import ValidationError
from models.user import User, UserRole
from voice.stt_client import SpeechToTextClient
from voice.tts_client import TextToSpeechClient
from voice.voice_session import RECORDINGS_DIR, VoiceSessionCoordinator


# ==========================================
# 1. Speech-to-Text Client Tests
# ==========================================

@pytest.mark.asyncio
@patch("voice.stt_client.websockets.connect")
async def test_stt_client_transcribe_stream(mock_ws_connect):
    # Set up mock websocket instance
    mock_ws = AsyncMock()
    mock_ws_connect.return_value.__aenter__.return_value = mock_ws

    client = SpeechToTextClient(api_key="el_test_key_123")

    # Mock server response messages over WebSocket
    mock_responses = [
        json.dumps({
            "message_type": "partial_transcript",
            "text": "Hello"
        }),
        json.dumps({
            "message_type": "final_transcript",
            "text": "Hello world",
            "confidence": 0.98
        }),
        json.dumps({
            "message_type": "session_ended"
        })
    ]
    
    # Mock ws.__aiter__ to return server responses asynchronously allowing sender to run
    async def mock_aiter():
        await asyncio.sleep(0.1)
        for res in mock_responses:
            yield res
    mock_ws.__aiter__.side_effect = mock_aiter

    # Input audio stream generator
    async def sample_audio_generator():
        yield b"chunk_one"
        yield b"chunk_two"

    updates = []
    async for update in client.transcribe_stream(sample_audio_generator()):
        updates.append(update)

    # Assertions
    # 1. Sent init config frame
    called_sent_msgs = [json.loads(call.args[0]) for call in mock_ws.send.call_args_list]
    assert called_sent_msgs[0]["message_type"] == "session_started"
    assert called_sent_msgs[0]["config"]["model_id"] == "scribe_v2_realtime"

    # 2. Sent audio frames
    assert called_sent_msgs[1]["message_type"] == "input_audio_chunk"
    assert base64.b64decode(called_sent_msgs[1]["audio_base_64"]) == b"chunk_one"
    assert base64.b64decode(called_sent_msgs[2]["audio_base_64"]) == b"chunk_two"

    # 3. Sent commit frame
    assert called_sent_msgs[3]["message_type"] == "input_audio_chunk"
    assert called_sent_msgs[3]["audio_base_64"] == ""
    assert called_sent_msgs[3]["commit"] is True

    # 4. Received transcripts
    assert len(updates) == 2
    assert updates[0]["type"] == "partial"
    assert updates[0]["text"] == "Hello"
    assert updates[1]["type"] == "final"
    assert updates[1]["text"] == "Hello world"
    assert updates[1]["confidence"] == 0.98


# ==========================================
# 2. Text-to-Speech Client Tests
# ==========================================

@pytest.mark.asyncio
@patch("voice.tts_client.AsyncElevenLabs")
async def test_tts_client_generate_speech_stream(mock_eleven_labs_class):
    # Set up mock ElevenLabs async client
    mock_client = MagicMock()
    mock_eleven_labs_class.return_value = mock_client

    # Mock async generator for streaming
    async def mock_audio_stream():
        yield b"audio_chunk_1"
        yield b"audio_chunk_2"

    mock_client.text_to_speech.stream = AsyncMock(return_value=mock_audio_stream())

    client = TextToSpeechClient(api_key="el_test_key_123")

    chunks = []
    async for chunk in client.generate_speech_stream(text="Synthesize me", voice_id="voice_id_xyz"):
        chunks.append(chunk)

    # Assertions
    assert len(chunks) == 2
    assert chunks[0] == b"audio_chunk_1"
    assert chunks[1] == b"audio_chunk_2"
    mock_client.text_to_speech.stream.assert_called_once_with(
        text="Synthesize me",
        voice_id="voice_id_xyz",
        model_id="eleven_flash_v2_5"
    )


# ==========================================
# 3. Session Coordinator & Privacy Tests
# ==========================================

@pytest.mark.asyncio
async def test_voice_session_privacy_opt_in():
    # Mock user who opted-in to voice history
    user_id = uuid.uuid4()
    mock_user = User(
        id=user_id,
        clerk_user_id="clerk_voice_test",
        email="voice_opt_in@test.com",
        role=UserRole.MEMBER,
        voice_profile_id="voice_rachel",
        voice_history_opt_in=True
    )

    # Mock clients
    mock_stt = AsyncMock(spec=SpeechToTextClient)
    async def mock_stt_stream(audio_generator, *args, **kwargs):
        async for _ in audio_generator:
            pass
        yield {"type": "partial", "text": "transcription"}
        yield {"type": "final", "text": "final transcription", "confidence": 0.99}
    mock_stt.transcribe_stream.side_effect = mock_stt_stream

    mock_tts = AsyncMock(spec=TextToSpeechClient)
    async def mock_tts_stream(*args, **kwargs):
        yield b"tts_out_chunk"
    mock_tts.generate_speech_stream.side_effect = mock_tts_stream

    coordinator = VoiceSessionCoordinator(stt_client=mock_stt, tts_client=mock_tts)

    # Input stream
    async def mock_input_mic():
        yield b"mic_bytes_1"
        yield b"mic_bytes_2"

    session_id = str(uuid.uuid4())
    audio_out = []
    async for chunk in coordinator.process_voice_turn(mock_user, mock_input_mic(), session_id=session_id):
        audio_out.append(chunk)

    # Assertions
    assert len(audio_out) == 1
    assert audio_out[0] == b"tts_out_chunk"

    # Verify audio file was saved to disk
    expected_filepath = os.path.join(RECORDINGS_DIR, str(user_id), f"{session_id}.pcm")
    assert os.path.exists(expected_filepath)
    
    # Read saved file to confirm exact bytes written
    with open(expected_filepath, "rb") as f:
        saved_bytes = f.read()
    assert saved_bytes == b"mic_bytes_1mic_bytes_2"

    # Clean up recording directory
    user_dir = os.path.join(RECORDINGS_DIR, str(user_id))
    if os.path.exists(user_dir):
        shutil.rmtree(user_dir)


@pytest.mark.asyncio
async def test_voice_session_privacy_opt_out():
    # Mock user who opted-out of voice history
    user_id = uuid.uuid4()
    mock_user = User(
        id=user_id,
        clerk_user_id="clerk_voice_test",
        email="voice_opt_out@test.com",
        role=UserRole.MEMBER,
        voice_profile_id="voice_rachel",
        voice_history_opt_in=False
    )

    # Mock clients
    mock_stt = AsyncMock(spec=SpeechToTextClient)
    async def mock_stt_stream(audio_generator, *args, **kwargs):
        async for _ in audio_generator:
            pass
        yield {"type": "final", "text": "final transcription", "confidence": 0.99}
    mock_stt.transcribe_stream.side_effect = mock_stt_stream

    mock_tts = AsyncMock(spec=TextToSpeechClient)
    async def mock_tts_stream(*args, **kwargs):
        yield b"tts_out_chunk"
    mock_tts.generate_speech_stream.side_effect = mock_tts_stream

    coordinator = VoiceSessionCoordinator(stt_client=mock_stt, tts_client=mock_tts)

    # Input stream
    async def mock_input_mic():
        yield b"mic_bytes_1"
        yield b"mic_bytes_2"

    session_id = str(uuid.uuid4())
    audio_out = []
    async for chunk in coordinator.process_voice_turn(mock_user, mock_input_mic(), session_id=session_id):
        audio_out.append(chunk)

    # Assertions
    assert len(audio_out) == 1
    assert audio_out[0] == b"tts_out_chunk"

    # Verify NO audio file was saved to disk
    expected_filepath = os.path.join(RECORDINGS_DIR, str(user_id), f"{session_id}.pcm")
    assert not os.path.exists(expected_filepath)
