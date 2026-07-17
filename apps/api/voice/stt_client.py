import asyncio
import base64
import json
import logging
from typing import AsyncGenerator, Optional, Dict, Any

import websockets
from core.config import settings
from core.exceptions import ValidationError

logger = logging.getLogger("voice.stt_client")

WS_URL = "wss://api.elevenlabs.io/v1/speech-to-text/realtime"


class SpeechToTextClient:
    """
    Streaming transcription client wrapping ElevenLabs Scribe v2 realtime WebSocket API.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.ELEVENLABS_API_KEY
        if not self.api_key or self.api_key == "el_xxxxxxxxxxxxxxxxxxxxx":
            logger.warning("ElevenLabs API Key is not configured. Realtime STT calls will fail.")

    async def transcribe_stream(
        self,
        audio_generator: AsyncGenerator[bytes, None],
        language_code: str = "en",
        sample_rate: int = 16000,
        audio_format: str = "pcm_16000",
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Connects to ElevenLabs Scribe WebSocket, streams audio chunks from audio_generator,
        and yields transcript updates (both partial and final).

        Yields:
            Dict: {
                "type": "partial" | "final",
                "text": str,
                "confidence": float (only for final)
            }
        """
        if not self.api_key or self.api_key == "el_xxxxxxxxxxxxxxxxxxxxx":
            raise ValidationError("Cannot run ElevenLabs Speech-to-Text: API Key is missing or default placeholder.")

        headers = {"xi-api-key": self.api_key}
        
        try:
            async with websockets.connect(WS_URL, extra_headers=headers) as ws:
                logger.info("Connected to ElevenLabs realtime STT WebSocket.")

                # 1. Send initial session configuration frame
                init_frame = {
                    "message_type": "session_started",
                    "config": {
                        "model_id": "scribe_v2_realtime",
                        "audio_format": audio_format,
                        "sample_rate": sample_rate,
                        "language_code": language_code,
                    }
                }
                await ws.send(json.dumps(init_frame))

                # Create a queue to hold items to yield back to the caller
                yield_queue = asyncio.Queue()

                # Define the sending task (reads from audio_generator, writes base64 to WebSocket)
                async def sender_task():
                    try:
                        async for chunk in audio_generator:
                            if not chunk:
                                continue
                            b64_audio = base64.b64encode(chunk).decode("utf-8")
                            audio_frame = {
                                "message_type": "input_audio_chunk",
                                "audio_base_64": b64_audio
                            }
                            await ws.send(json.dumps(audio_frame))
                            # Yield control to prevent CPU/event-loop starvation
                            await asyncio.sleep(0.001)

                        # End of stream reached: send commit frame
                        commit_frame = {
                            "message_type": "input_audio_chunk",
                            "audio_base_64": "",
                            "commit": True
                        }
                        await ws.send(json.dumps(commit_frame))
                        logger.info("Finished streaming audio chunks, sent commit frame.")
                    except asyncio.CancelledError:
                        pass
                    except Exception as e:
                        logger.error(f"Error in STT sender task: {str(e)}")
                        await yield_queue.put({"error": str(e)})

                # Define the receiving task (reads from WebSocket, puts transcripts into yield_queue)
                async def receiver_task():
                    try:
                        async for message in ws:
                            data = json.loads(message)
                            message_type = data.get("message_type")
                            
                            if message_type == "partial_transcript":
                                await yield_queue.put({
                                    "type": "partial",
                                    "text": data.get("text", "")
                                })
                            elif message_type == "final_transcript" or message_type == "transcript":
                                # Scribe may return "final_transcript" or standard "transcript"
                                await yield_queue.put({
                                    "type": "final",
                                    "text": data.get("text", ""),
                                    "confidence": data.get("confidence", 1.0)
                                })
                            elif message_type == "session_ended":
                                logger.info("STT session ended by server.")
                                break
                    except asyncio.CancelledError:
                        pass
                    except Exception as e:
                        logger.error(f"Error in STT receiver task: {str(e)}")
                        await yield_queue.put({"error": str(e)})
                    finally:
                        # Put None to signal end of stream to consumer
                        await yield_queue.put(None)

                # Launch sender & receiver concurrently
                st_task = asyncio.create_task(sender_task())
                rc_task = asyncio.create_task(receiver_task())

                try:
                    # Retrieve and yield transcripts from the queue
                    while True:
                        item = await yield_queue.get()
                        if item is None:
                            break
                        if "error" in item:
                            raise RuntimeError(f"STT stream failed: {item['error']}")
                        yield item
                finally:
                    # Clean up background tasks
                    st_task.cancel()
                    rc_task.cancel()
                    await asyncio.gather(st_task, rc_task, return_exceptions=True)

        except websockets.exceptions.WebSocketException as e:
            logger.exception("ElevenLabs STT WebSocket connection error")
            raise RuntimeError(f"STT WebSocket failure: {str(e)}")
        except Exception as e:
            logger.exception("STT processing error occurred")
            raise
