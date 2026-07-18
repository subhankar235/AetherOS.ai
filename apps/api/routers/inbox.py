import logging
from fastapi import APIRouter, Request, HTTPException

from core.config import settings
from workers.email_processor import process_gmail_notification

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger("routers.inbox")


@router.post("/gmail")
async def gmail_webhook(request: Request):
    """
    Receives Google Pub/Sub push notifications.
    Verifies the pre-shared secret token, acknowledges fast,
    and enqueues the payload to a Celery background queue.
    """
    token = request.query_params.get("token")
    if not token:
        token = request.headers.get("X-PubSub-Token")

    if not token or token != settings.GOOGLE_PUBSUB_VERIFICATION_TOKEN:
        logger.warning("Rejected unauthorized Gmail webhook call (invalid/missing token)")
        raise HTTPException(status_code=401, detail="Unauthorized webhook source")

    try:
        payload = await request.json()
    except Exception as exc:
        logger.error(f"Malformed Gmail webhook JSON payload: {exc}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Enqueue task asynchronously in Celery
    process_gmail_notification.delay(payload)

    return {"status": "enqueued"}
