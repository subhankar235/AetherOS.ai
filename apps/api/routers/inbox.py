import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.deps import get_current_user
from core.exceptions import ExternalServiceError
from db.session import get_db
from schemas.email_schema import EmailMetadataResponse
from models.email_metadata import EmailMetadata
from models.user import User
from integrations.gmail_client import search_messages, fetch_message, get_thread as gmail_get_thread
from agents.inbox_agent.search import natural_language_search
from agents.inbox_agent.reader import read_email, summarize_thread
from workers.email_processor import process_gmail_notification

logger = logging.getLogger("routers.inbox")

router = APIRouter(tags=["inbox"])


@router.post("/webhooks/gmail")
async def gmail_webhook(request: Request):
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

    process_gmail_notification.delay(payload)

    return {"status": "enqueued"}


@router.get("/inbox/emails", response_model=list[EmailMetadataResponse])
async def list_emails(
    priority: Optional[str] = Query(None, description="Filter by priority: High, Medium, Low"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        stmt = select(EmailMetadata).where(EmailMetadata.user_id == user.id)

        if priority:
            stmt = stmt.where(EmailMetadata.priority == priority)
        if category:
            stmt = stmt.where(EmailMetadata.category == category)

        stmt = stmt.order_by(desc(EmailMetadata.received_at)).offset(offset).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Failed to list emails for user {user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve emails")


@router.get("/inbox/emails/{email_id}", response_model=EmailMetadataResponse)
async def get_email(
    email_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(EmailMetadata).where(
            EmailMetadata.id == email_id,
            EmailMetadata.user_id == user.id,
        )
    )
    email = result.scalar_one_or_none()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return email


@router.get("/inbox/search")
async def search_inbox(
    q: str = Query(..., description="Natural language search query"),
    page_token: Optional[str] = Query(None),
    limit: int = Query(25, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        results = await natural_language_search(
            user_id=user.id,
            query=q,
            page_token=page_token,
            db=db,
        )
        return results
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Email search failed for user {user.id}: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/inbox/read/{gmail_message_id}")
async def read_gmail_message(
    gmail_message_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        message_data = await read_email(
            user_id=user.id,
            message_id=gmail_message_id,
            db=db,
        )
        return message_data
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to read email {gmail_message_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to read email")


@router.get("/inbox/thread/{gmail_thread_id}")
async def get_thread(
    gmail_thread_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        thread_data = await summarize_thread(
            user_id=user.id,
            thread_id=gmail_thread_id,
            db=db,
        )
        return thread_data
    except ExternalServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get thread {gmail_thread_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve thread")
