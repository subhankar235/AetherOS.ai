import logging
from typing import AsyncGenerator, Optional

from elevenlabs.client import AsyncElevenLabs
from core.config import settings
from core.exceptions import ValidationError

logger = logging.getLogger("voice.tts_client")


class TextToSpeechClient:
    """
    Client wrapper around ElevenLabs Text-to-Speech (TTS) async streaming API.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.ELEVENLABS_API_KEY
        if not self.api_key or self.api_key == "el_xxxxxxxxxxxxxxxxxxxxx":
            logger.warning("ElevenLabs API Key is not configured. TTS calls will fail.")
        
        # Initialize ElevenLabs async client
        self.client = AsyncElevenLabs(api_key=self.api_key)

    async def generate_speech_stream(
        self,
        text: str,
        voice_id: Optional[str] = None,
        model_id: Optional[str] = None,
    ) -> AsyncGenerator[bytes, None]:
        """
        Calls ElevenLabs TTS stream generation to convert text into speech.

        Args:
            text: The text string to synthesize.
            voice_id: ElevenLabs voice profile ID. Defaults to settings.ELEVENLABS_DEFAULT_VOICE_ID.
            model_id: ElevenLabs model ID. Defaults to settings.ELEVENLABS_DEFAULT_MODEL_ID.

        Yields:
            bytes: Audio chunks.
        """
        if not self.api_key or self.api_key == "el_xxxxxxxxxxxxxxxxxxxxx":
            raise ValidationError("Cannot run ElevenLabs Text-to-Speech: API Key is missing or default placeholder.")

        resolved_voice_id = voice_id or settings.ELEVENLABS_DEFAULT_VOICE_ID
        resolved_model_id = model_id or settings.ELEVENLABS_DEFAULT_MODEL_ID

        logger.info(f"Generating voice using voice_id '{resolved_voice_id}' and model '{resolved_model_id}'...")

        try:
            # client.text_to_speech.stream returns an AsyncIterator yielding bytes
            audio_generator = await self.client.text_to_speech.stream(
                text=text,
                voice_id=resolved_voice_id,
                model_id=resolved_model_id
            )

            async for chunk in audio_generator:
                if isinstance(chunk, bytes):
                    yield chunk

        except Exception as e:
            logger.exception("ElevenLabs Text-to-Speech conversion failed")
            raise RuntimeError(f"TTS conversion failure: {str(e)}")
