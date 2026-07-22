import asyncio
import base64
import json
import logging
import uuid

from core.celery_app import celery_app
from db.session import AsyncSessionLocal

logger = logging.getLogger("workers.email_processor")


async def _process_notification(payload: dict) -> dict:
    message_data = payload.get("message", {})
    raw_data = message_data.get("data", "")
    if not raw_data:
        logger.warning("PubSub payload missing 'message.data'")
        return {"status": "skipped", "reason": "missing_data"}

    decoded = base64.urlsafe_b64decode(raw_data).decode("utf-8")
    notification = json.loads(decoded)

    email_address = notification.get("emailAddress", "")
    history_id = notification.get("historyId", "")

    logger.info(f"PubSub notification: email={email_address}, historyId={history_id}")

    async with AsyncSessionLocal() as db:
        from models.user import User
        from sqlalchemy import select

        user_result = await db.execute(
            select(User).where(User.email == email_address)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            logger.warning(f"No local user found for email {email_address}")
            return {"status": "skipped", "reason": "no_user", "email": email_address}

        from integrations.gmail_client import search_messages
        from agents.inbox_agent.auto_pipeline import process_new_email

        history_query = f"after:history_id:{history_id}"
        try:
            history_result = await search_messages(user.id, "", None, db)
            messages = history_result.get("messages", [])
        except Exception as exc:
            logger.warning(f"Failed to query messages for history {history_id}: {exc}")
            messages = []

        processed = 0
        for msg in messages[:50]:
            try:
                msg_id = msg["id"]
                await process_new_email(user.id, msg_id, db)
                processed += 1
            except Exception as exc:
                logger.exception(f"Failed to process message {msg.get('id')}: {exc}")

        logger.info(f"Processed {processed} messages from history {history_id}")
        return {
            "status": "completed",
            "email": email_address,
            "history_id": history_id,
            "processed": processed,
        }


@celery_app.task(name="workers.email_processor.process_gmail_notification", bind=True, max_retries=3)
def process_gmail_notification(self, payload: dict) -> dict:
    try:
        result = asyncio.run(_process_notification(payload))
        return result
    except Exception as exc:
        logger.exception(f"Failed to process Gmail notification: {exc}")
        try:
            self.retry(countdown=60)
        except Exception:
            pass
        return {"status": "error", "error": str(exc)}
