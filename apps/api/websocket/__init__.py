import logging
from typing import Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from core.config import settings
from core.exceptions import AuthError
from core.security import verify_clerk_session
from db.session import AsyncSessionLocal
from models.user import User, UserRole
from websocket.connection_manager import connection_manager
from websocket.events import event_broadcaster

logger = logging.getLogger("websocket")

router = APIRouter()


async def _verify_ws_token(token: str) -> Optional[User]:
    if not token:
        return None

    is_dev = settings.APP_ENV == "development" and token.startswith("dev-token-")

    if is_dev:
        email = token.removeprefix("dev-token-").strip()
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            if user:
                return user
            import uuid
            user = User(
                id=uuid.uuid4(),
                clerk_user_id=f"clerk_dev_{email.split('@')[0]}",
                email=email,
                role=UserRole.MEMBER,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user

    try:
        claims = verify_clerk_session(token)
    except AuthError:
        return None

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.clerk_user_id == claims.user_id)
        )
        return result.scalar_one_or_none()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(""),
):
    user = await _verify_ws_token(token)
    if user is None:
        await websocket.close(code=4001, reason="Unauthorized: invalid or missing Clerk token")
        return

    user_id_str = str(user.id)
    await connection_manager.connect(user_id_str, websocket)

    try:
        await websocket.send_json({
            "type": "connected",
            "user_id": user_id_str,
            "message": "Real-time connection established",
        })

        while True:
            try:
                data = await websocket.receive_text()
            except WebSocketDisconnect:
                break

            if data == "ping":
                await websocket.send_json({"type": "pong"})
            else:
                logger.debug(f"Unhandled WS message from {user_id_str}: {data[:100]}")

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.warning(f"WebSocket error for user {user_id_str}: {exc}")
    finally:
        await connection_manager.disconnect(user_id_str, websocket)
