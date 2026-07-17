import logging
from core.celery_app import celery_app

logger = logging.getLogger("workers.email_processor")


@celery_app.task(name="workers.email_processor.process_gmail_notification")
def process_gmail_notification(payload: dict) -> None:
    """
    Stub background task to process Gmail Pub/Sub push notifications.
    To be fully implemented in Phase 11.
    """
    logger.info(f"Received Gmail Pub/Sub notification payload: {payload}")
