import asyncio
import logging
import os
import uuid
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.user import User
from voice.stt_client import SpeechToTextClient
from voice.tts_client import TextToSpeechClient

logger = logging.getLogger("voice.voice_session")

RECORDINGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "voice_recordings"))


class VoiceSessionCoordinator:
    """
    Orchestrates a single voice turn:
    audio in -> STT -> Supervisor (stubbed) -> Human Voice Layer (stubbed) -> TTS -> audio out.
    Enforces privacy by saving audio files to disk only if users.voice_history_opt_in is true.
    """

    def __init__(
        self,
        stt_client: Optional[SpeechToTextClient] = None,
        tts_client: Optional[TextToSpeechClient] = None,
    ):
        self.stt_client = stt_client or SpeechToTextClient()
        self.tts_client = tts_client or TextToSpeechClient()

    async def _save_and_yield_audio(
        self,
        audio_stream: AsyncGenerator[bytes, None],
        filepath: str
    ) -> AsyncGenerator[bytes, None]:
        """
        Helper generator that writes audio stream chunks to disk while yielding them.
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        try:
            with open(filepath, "wb") as f:
                async for chunk in audio_stream:
                    f.write(chunk)
                    yield chunk
            logger.info(f"Successfully persisted voice recording to: {filepath}")
        except Exception as e:
            logger.error(f"Failed to write recording to disk: {str(e)}")
            # Fallback: yield the rest of the chunks even if disk write fails
            async for chunk in audio_stream:
                yield chunk

    async def process_voice_turn(
        self,
        user: User,
        audio_stream: AsyncGenerator[bytes, None],
        session_id: Optional[str] = None
    ) -> AsyncGenerator[bytes, None]:
        """
        Orchestrates the voice session turn:
        1. Transcribe incoming audio using SpeechToTextClient.
        2. Save recording if user.voice_history_opt_in is True, else stream in-memory only.
        3. Handoff transcript to Supervisor (stubbed).
        4. Apply Human Voice Layer (stubbed).
        5. Return the resulting TTS stream.
        """
        active_session = session_id or str(uuid.uuid4())
        
        # 1. Determine recording pathway based on user's privacy opt-in setting
        if user.voice_history_opt_in:
            filename = f"{active_session}.pcm"
            filepath = os.path.join(RECORDINGS_DIR, str(user.id), filename)
            logger.info(f"User '{user.email}' opted in to voice history. Recording will be saved to disk.")
            processing_stream = self._save_and_yield_audio(audio_stream, filepath)
        else:
            logger.info(f"User '{user.email}' opted out of voice history. Processing stream purely in volatile memory.")
            processing_stream = audio_stream

        # 2. Run speech-to-text transcription
        final_transcript = ""
        try:
            async for update in self.stt_client.transcribe_stream(processing_stream):
                if update.get("type") == "final":
                    final_transcript = update.get("text", "").strip()
        except Exception as e:
            logger.error(f"STT execution failed in voice session coordinator: {str(e)}")
            raise

        if not final_transcript:
            logger.warning("Voice session received empty transcription. Returning silence.")
            return

        logger.info(f"Speech transcription finalized: '{final_transcript}'")

        # 3. Handoff to Supervisor Agent
        from agents.supervisor import supervisor_graph
        from agents.supervisor.context_manager import get_default_context
        context = getattr(user, "voice_context", None) or get_default_context()

        response_data = await supervisor_graph.run(
            user_id=str(user.id),
            session_id=active_session,
            raw_input=final_transcript,
            input_mode="voice",
            conversation_context=context,
        )
        logger.info(f"Supervisor Agent response: {response_data}")

        # 4. Apply Human Voice Layer turn re-writing
        from voice.conversational_rewrite import rewrite
        rewritten_response = rewrite(response_data, context=context)
        logger.info(f"Human Voice Layer rewritten response: '{rewritten_response}'")

        # 5. Synthesize TTS output stream
        voice_id = user.voice_profile_id or settings.ELEVENLABS_DEFAULT_VOICE_ID
        try:
            async for audio_chunk in self.tts_client.generate_speech_stream(
                text=rewritten_response,
                voice_id=voice_id
            ):
                yield audio_chunk
        except Exception as e:
            logger.error(f"TTS execution failed in voice session coordinator: {str(e)}")
            raise
