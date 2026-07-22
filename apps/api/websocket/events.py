import asyncio
import json
import logging
from typing import Any, Optional

from core.config import settings
from websocket.connection_manager import connection_manager

logger = logging.getLogger("websocket.events")

REDIS_CHANNEL_PATTERN = "dashboard:*"


class EventBroadcaster:
    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._listen_loop())
        logger.info("EventBroadcaster started — listening on dashboard:*")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("EventBroadcaster stopped")

    async def _listen_loop(self) -> None:
        while self._running:
            try:
                await self._listen()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning(f"Redis listener error, reconnecting in 3s: {exc}")
                await asyncio.sleep(3)

    async def _listen(self) -> None:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.REDIS_URL)
        try:
            pubsub = r.pubsub()
            await pubsub.psubscribe(REDIS_CHANNEL_PATTERN)
            logger.info("Subscribed to dashboard:* Redis channels")

            async for message in pubsub.listen():
                if not self._running:
                    break
                if message["type"] != "pmessage":
                    continue

                channel: str = message.get("channel", b"").decode() if isinstance(message.get("channel"), bytes) else str(message.get("channel", ""))
                data: str = message.get("data", b"").decode() if isinstance(message.get("data"), bytes) else str(message.get("data", ""))

                user_id = self._parse_user_id(channel)
                if not user_id:
                    continue

                try:
                    event = json.loads(data)
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Invalid JSON on {channel}: {data[:200]}")
                    continue

                await connection_manager.broadcast_to_user(user_id, event)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception(f"Redis listener failed: {exc}")
            raise
        finally:
            try:
                await r.close()
            except Exception:
                pass

    @staticmethod
    def _parse_user_id(channel: str) -> Optional[str]:
        prefix = "dashboard:"
        if channel.startswith(prefix):
            return channel[len(prefix):]
        return None


event_broadcaster = EventBroadcaster()
