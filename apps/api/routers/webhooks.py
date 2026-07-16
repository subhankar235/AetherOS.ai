# routers/webhooks.py
"""
Receives Clerk's user.created / user.updated / user.deleted events and
syncs the local `users` table. This is the primary sync mechanism —
get_current_user() (core/deps.py) treats a missing user as an auth error
rather than lazily creating one, so this endpoint must be reliable.
"""

from fastapi import APIRouter, Request, HTTPException

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from core.security import verify_webhook_signature
from core.config import settings
from db.session import get_db
from models.user import User

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/clerk")
async def clerk_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload_body = await request.body()
    headers = dict(request.headers)

    try:
        event = verify_webhook_signature(
            payload_body, headers, settings.clerk_webhook_signing_secret
        )
    except Exception:
        # Any verification failure -> reject outright, don't try to be helpful
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    event_type = event.get("type")
    data = event.get("data", {})

    if event_type == "user.created":
        await _handle_user_created(db, data)
    elif event_type == "user.updated":
        await _handle_user_updated(db, data)
    elif event_type == "user.deleted":
        await _handle_user_deleted(db, data)
    # Unrecognized event types are ignored, not errors — Clerk may add
    # new event types later that this endpoint doesn't need to act on.

    return {"received": True}


async def _handle_user_created(db: AsyncSession, data: dict):
    clerk_user_id = data["id"]
    email = _primary_email(data)
    name = _full_name(data)

    existing = await db.execute(select(User).where(User.clerk_user_id == clerk_user_id))
    if existing.scalar_one_or_none():
        return  # idempotent — Clerk may redeliver

    db.add(User(clerk_user_id=clerk_user_id, email=email, name=name))
    await db.commit()


async def _handle_user_updated(db: AsyncSession, data: dict):
    clerk_user_id = data["id"]
    result = await db.execute(select(User).where(User.clerk_user_id == clerk_user_id))
    user = result.scalar_one_or_none()
    if user is None:
        # Out-of-order delivery — create it now rather than dropping the update.
        await _handle_user_created(db, data)
        return

    user.email = _primary_email(data)
    user.name = _full_name(data)
    await db.commit()


async def _handle_user_deleted(db: AsyncSession, data: dict):
    clerk_user_id = data["id"]
    result = await db.execute(select(User).where(User.clerk_user_id == clerk_user_id))
    user = result.scalar_one_or_none()
    if user is None:
        return

    # Cascade per your retention policy. Minimal version: hard delete.
    # If you need GDPR export-before-delete, do that here before removing the row.
    await db.delete(user)
    await db.commit()


def _primary_email(data: dict) -> str:
    for entry in data.get("email_addresses", []):
        if entry.get("id") == data.get("primary_email_address_id"):
            return entry["email_address"]
    # Fallback: first email on the account
    emails = data.get("email_addresses", [])
    return emails[0]["email_address"] if emails else ""


def _full_name(data: dict) -> str | None:
    first = data.get("first_name") or ""
    last = data.get("last_name") or ""
    full = f"{first} {last}".strip()
    return full or None