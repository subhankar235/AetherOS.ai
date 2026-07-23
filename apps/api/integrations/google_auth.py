import asyncio
import uuid
from datetime import datetime, timezone
import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from google.auth.exceptions import RefreshError

from core.config import settings
from core.security import decrypt_token, encrypt_token
from core.exceptions import IntegrationAuthRequiredError
from models.google_integration import GoogleIntegration

logger = logging.getLogger("integrations.google_auth")


class GoogleScopes:
    GMAIL_SEND = "https://www.googleapis.com/auth/gmail.send"
    GMAIL_MODIFY = "https://www.googleapis.com/auth/gmail.modify"
    GMAIL_COMPOSE = "https://www.googleapis.com/auth/gmail.compose"
    CALENDAR = "https://www.googleapis.com/auth/calendar"

    BASE = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/gmail.compose",
        "https://www.googleapis.com/auth/calendar",
    ]


def check_scopes_granted(integration: GoogleIntegration, required_scopes: list[str]) -> bool:
    """
    Checks if all required scopes have been granted in the integration.
    """
    if not required_scopes:
        return True
    if not integration.scopes:
        return True
    granted = set(integration.scopes or [])
    return all(scope in granted for scope in required_scopes)



async def refresh_google_credentials(
    db: AsyncSession,
    integration: GoogleIntegration
) -> Credentials:
    """
    Refreshes the Google OAuth credentials if they have expired.
    Updates the database with the new access token and commits.
    Raises IntegrationAuthRequiredError if the refresh token is revoked.
    """
    # 1. Decrypt access and refresh tokens
    try:
        decrypted_access = decrypt_token(integration.access_token)
        decrypted_refresh = decrypt_token(integration.refresh_token)
    except Exception as exc:
        logger.exception("Failed to decrypt stored Google tokens")
        raise IntegrationAuthRequiredError("Google tokens are corrupted. Please reconnect.") from exc

    # 2. Build Credentials object
    creds_expiry = integration.expires_at
    if creds_expiry.tzinfo is not None:
        creds_expiry = creds_expiry.astimezone(timezone.utc).replace(tzinfo=None)

    creds = Credentials(
        token=decrypted_access,
        refresh_token=decrypted_refresh,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=integration.scopes,
        expiry=creds_expiry
    )

    # 3. Check if expired
    if creds.expired:
        logger.info(f"Google access token for user {integration.user_id} expired. Refreshing...")
        try:
            await asyncio.wait_for(asyncio.to_thread(creds.refresh, GoogleRequest()), timeout=8.0)
        except (RefreshError, asyncio.TimeoutError) as exc:
            logger.warning(f"Google refresh token revoked, invalid, or timed out for user {integration.user_id}: {exc}")
            # Mark integration as revoked in DB
            integration.revoked_at = datetime.now(timezone.utc)
            await db.commit()
            raise IntegrationAuthRequiredError("Google connection has expired or been revoked. Please reconnect.") from exc
        
        # 4. Save refreshed tokens back to database
        try:
            integration.access_token = encrypt_token(creds.token)
            # Some identity providers rotate refresh tokens on refresh, check if updated
            if creds.refresh_token and creds.refresh_token != decrypted_refresh:
                integration.refresh_token = encrypt_token(creds.refresh_token)
            
            # Make sure we save it as a timezone-aware UTC datetime
            if not creds.expiry:
                raise IntegrationAuthRequiredError("Refreshed token has no expiry")
            integration.expires_at = creds.expiry.replace(tzinfo=timezone.utc)
            await db.commit()
            logger.info(f"Google access token refreshed and saved successfully for user {integration.user_id}")
        except Exception as exc:
            logger.exception("Failed to save refreshed Google tokens to database")
            await db.rollback()

    return creds


async def get_google_credentials(
    user_id: uuid.UUID,
    db: AsyncSession,
    required_scopes: Optional[list[str]] = None
) -> Credentials:
    """
    Retrieves and refreshes Google Credentials for the given user ID.
    Raises IntegrationAuthRequiredError if the connection is missing,
    revoked, or if required scopes are missing.
    """
    result = await db.execute(
        select(GoogleIntegration).where(GoogleIntegration.user_id == user_id)
    )
    integration = result.scalar_one_or_none()

    if not integration or integration.revoked_at is not None:
        # Fallback: check if there is an active GoogleIntegration in the DB for single-tenant / dev environments
        fallback_res = await db.execute(
            select(GoogleIntegration).where(GoogleIntegration.revoked_at.is_(None)).order_by(GoogleIntegration.created_at.desc())
        )
        integration = fallback_res.scalars().first()

    if not integration or integration.revoked_at is not None:
        raise IntegrationAuthRequiredError("Google account is not connected. Please connect Google.")

    if required_scopes and not check_scopes_granted(integration, required_scopes):
        # Determine missing scopes for client context
        missing = [s for s in required_scopes if s not in integration.scopes]
        raise IntegrationAuthRequiredError(
            message="Additional Google authorization is required for this action.",
            details={"missing_scopes": missing}
        )

    return await refresh_google_credentials(db, integration)
