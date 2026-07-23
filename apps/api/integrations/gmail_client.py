import uuid
import base64
import logging
from email.mime.text import MIMEText
from sqlalchemy.ext.asyncio import AsyncSession
from googleapiclient.discovery import build
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import settings
from core.limiter import limiter
from integrations.google_auth import get_google_credentials, GoogleScopes

logger = logging.getLogger("integrations.gmail_client")

# Retry logic: retry up to 3 times with exponential backoff
gmail_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)


async def _get_gmail_service(user_id: uuid.UUID, db: AsyncSession, required_scopes: list[str]):
    """
    Helper to get the authorized Google Gmail API service.
    """
    creds = await get_google_credentials(user_id, db, required_scopes)
    return build("gmail", "v1", credentials=creds)


@gmail_retry
async def fetch_message(user_id: uuid.UUID, message_id: str, db: AsyncSession) -> dict:
    """
    Fetches a single Gmail message by ID.
    """
    await limiter.check_rate_limit(f"gmail:{user_id}", limit=settings.RATE_LIMIT_GMAIL_PER_MIN, period=60)
    service = await _get_gmail_service(user_id, db, [GoogleScopes.BASE[3]])
    
    # Run synchronous execution in an executor or execute directly (async-compatible thread safety)
    return service.users().messages().get(userId="me", id=message_id, format="full").execute()


@gmail_retry
async def search_messages(user_id: uuid.UUID, query: str, page_token: str | None, db: AsyncSession) -> dict:
    """
    Searches Gmail messages based on query.
    """
    await limiter.check_rate_limit(f"gmail:{user_id}", limit=settings.RATE_LIMIT_GMAIL_PER_MIN, period=60)
    service = await _get_gmail_service(user_id, db, [GoogleScopes.BASE[3]])
    
    kwargs = {"userId": "me", "q": query}
    if page_token:
        kwargs["pageToken"] = page_token
        
    return service.users().messages().list(**kwargs).execute()


@gmail_retry
async def send_message(
    user_id: uuid.UUID,
    to: str,
    subject: str,
    body: str,
    thread_id: str | None,
    db: AsyncSession
) -> dict:
    """
    Sends a MIME-formatted email.
    """
    from googleapiclient.errors import HttpError
    from core.exceptions import IntegrationAuthRequiredError

    await limiter.check_rate_limit(f"gmail:{user_id}", limit=settings.RATE_LIMIT_GMAIL_PER_MIN, period=60)
    service = await _get_gmail_service(user_id, db, [GoogleScopes.GMAIL_SEND])
    
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    payload = {"raw": raw_message}
    if thread_id:
        payload["threadId"] = thread_id

    try:
        return service.users().messages().send(userId="me", body=payload).execute()
    except HttpError as exc:
        if exc.resp.status in (401, 403) and ("insufficient" in str(exc).lower() or "scope" in str(exc).lower()):
            logger.warning(f"Google API send failed due to insufficient permissions for user {user_id}: {exc}")
            raise IntegrationAuthRequiredError(
                "Google Account missing email send permission. Please go to Settings -> Integrations and click 'Reconnect Google' to grant full send access."
            ) from exc
        raise


@gmail_retry
async def create_draft(
    user_id: uuid.UUID,
    thread_id: str | None,
    body: str,
    db: AsyncSession
) -> dict:
    """
    Creates a new draft email.
    """
    await limiter.check_rate_limit(f"gmail:{user_id}", limit=settings.RATE_LIMIT_GMAIL_PER_MIN, period=60)
    service = await _get_gmail_service(user_id, db, [GoogleScopes.GMAIL_COMPOSE])
    
    message = MIMEText(body)
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    payload = {
        "message": {
            "raw": raw_message
        }
    }
    if thread_id:
        payload["message"]["threadId"] = thread_id
        
    return service.users().drafts().create(userId="me", body=payload).execute()


@gmail_retry
async def list_labels(user_id: uuid.UUID, db: AsyncSession) -> dict:
    """
    Lists Gmail labels for the user.
    """
    await limiter.check_rate_limit(f"gmail:{user_id}", limit=settings.RATE_LIMIT_GMAIL_PER_MIN, period=60)
    service = await _get_gmail_service(user_id, db, [GoogleScopes.BASE[3]])
    
    return service.users().labels().list(userId="me").execute()


@gmail_retry
async def get_thread(user_id: uuid.UUID, thread_id: str, db: AsyncSession) -> dict:
    """
    Gets a message thread by ID.
    """
    await limiter.check_rate_limit(f"gmail:{user_id}", limit=settings.RATE_LIMIT_GMAIL_PER_MIN, period=60)
    service = await _get_gmail_service(user_id, db, [GoogleScopes.BASE[3]])
    
    return service.users().threads().get(userId="me", id=thread_id).execute()


@gmail_retry
async def watch_inbox(user_id: uuid.UUID, topic_name: str, db: AsyncSession) -> dict:
    """
    Registers a Pub/Sub topic to watch Inbox events.
    """
    await limiter.check_rate_limit(f"gmail:{user_id}", limit=settings.RATE_LIMIT_GMAIL_PER_MIN, period=60)
    service = await _get_gmail_service(user_id, db, [GoogleScopes.BASE[3]])
    
    body = {
        "topicName": topic_name,
        "labelIds": ["INBOX"]
    }
    return service.users().watch(userId="me", body=body).execute()
