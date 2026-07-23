import json
import logging
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user
from core.exceptions import ExternalServiceError
from db.session import get_db
from models.user import User
from agents.supervisor import supervisor_graph
from agents.supervisor.context_manager import get_default_context
from voice.stt_client import SpeechToTextClient
from voice.tts_client import TextToSpeechClient

logger = logging.getLogger("routers.command_center")

router = APIRouter(prefix="/command", tags=["command_center"])

stt_client = SpeechToTextClient()
tts_client = TextToSpeechClient()


_IN_MEMORY_CONTEXTS: dict[str, dict] = {}


async def _load_session_context(session_id: str) -> dict[str, Any]:
    try:
        import redis.asyncio as aioredis
        from core.config import settings
        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        raw = await r.get(f"session_context:{session_id}")
        await r.close()
        if raw:
            return json.loads(raw)
    except Exception as e:
        logger.warning(f"Redis context fetch skipped: {e}")

    return _IN_MEMORY_CONTEXTS.get(session_id, get_default_context())


async def _save_session_context(session_id: str, context: dict[str, Any]) -> None:
    _IN_MEMORY_CONTEXTS[session_id] = context
    try:
        import redis.asyncio as aioredis
        from core.config import settings
        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await r.set(f"session_context:{session_id}", json.dumps(context), ex=86400)
        await r.close()
    except Exception as e:
        logger.warning(f"Redis context save skipped: {e}")


@router.post("")
async def text_command(
    command: str = Form(..., description="Natural language command text"),
    session_id: Optional[str] = Form(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    active_session = session_id or str(uuid.uuid4())
    context = await _load_session_context(active_session)

    try:
        response_data = await supervisor_graph.run(
            user_id=str(user.id),
            session_id=active_session,
            raw_input=command,
            input_mode="text",
            conversation_context=context,
        )

        if isinstance(response_data, dict) and "conversation_context" in response_data:
            await _save_session_context(active_session, response_data["conversation_context"])

        # Determine result type based on response content (simple heuristic)
        result_type = "default"
        if isinstance(response_data, dict):
            # If the response contains items, assume it's a query result
            if response_data.get("result", {}).get("items"):
                result_type = "query"
        from fastapi.responses import JSONResponse
        return JSONResponse(
            content={"session_id": active_session, "response": response_data},
            headers={"X-Result-Type": result_type},
        )
    except Exception as e:
        logger.exception(f"Supervisor failed for command: {command[:80]}")
        raise HTTPException(status_code=500, detail=f"Command processing failed: {str(e)}")


@router.post("/voice")
async def voice_command(
    audio: UploadFile = File(..., description="Audio file for speech-to-text"),
    session_id: Optional[str] = Form(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    active_session = session_id or str(uuid.uuid4())

    try:
        audio_bytes = await audio.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read audio file: {str(e)}")

    async def audio_generator():
        yield audio_bytes

    try:
        final_transcript = ""
        async for update in stt_client.transcribe_stream(audio_generator()):
            if update.get("type") == "final":
                final_transcript = update.get("text", "").strip()
    except Exception as e:
        logger.error(f"STT failed for voice command: {e}")
        raise HTTPException(status_code=502, detail=f"Speech-to-text failed: {str(e)}")

    if not final_transcript:
        raise HTTPException(status_code=400, detail="No speech detected in audio")

    context = get_default_context()

    try:
        response = await supervisor_graph.run(
            user_id=str(user.id),
            session_id=active_session,
            raw_input=final_transcript,
            input_mode="voice",
            conversation_context=context,
        )
        return {
            "session_id": active_session,
            "transcript": final_transcript,
            "response": response,
        }
    except Exception as e:
        logger.exception(f"Supervisor failed for voice command: {final_transcript[:80]}")
        raise HTTPException(status_code=500, detail=f"Voice command processing failed: {str(e)}")
