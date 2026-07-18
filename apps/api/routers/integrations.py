import uuid
from datetime import datetime, timezone
import logging
from typing import Optional
import secrets
import hashlib
import base64

from fastapi import APIRouter, Depends, Request, Response, HTTPException, Query
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from google_auth_oauthlib.flow import Flow

from core.config import settings
from core.deps import get_current_user
from core.security import generate_oauth_state, verify_oauth_state, encrypt_token
from db.session import get_db
from models.user import User
from models.google_integration import GoogleIntegration
from integrations.google_auth import GoogleScopes

router = APIRouter(prefix="/integrations", tags=["integrations"])
logger = logging.getLogger("routers.integrations")


def generate_pkce() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    sha256_hash = hashlib.sha256(verifier.encode("utf-8")).digest()
    challenge = base64.urlsafe_b64encode(sha256_hash).decode("utf-8").replace("=", "")
    return verifier, challenge


@router.get("/google/connect")
async def google_connect(
    request: Request,
    scopes: Optional[str] = Query(None, description="Comma-separated scopes to request"),
    user: User = Depends(get_current_user)
):
    """
    Builds the Google OAuth connection URL with PKCE and state protection,
    redirects the user, and sets the code verifier cookie.
    """
    # Parse requested scopes or default to BASE
    scope_list = GoogleScopes.BASE.copy()
    if scopes:
        for s in scopes.split(","):
            s_clean = s.strip()
            if s_clean and s_clean not in scope_list:
                scope_list.append(s_clean)

    # Create PKCE verifier and challenge
    verifier, challenge = generate_pkce()

    # Generate secure state
    state = generate_oauth_state(str(user.id))

    # Build OAuth URL using Google Flow client config
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=scope_list,
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )

    auth_url, _ = flow.authorization_url(
        state=state,
        code_challenge=challenge,
        code_challenge_method="S256",
        access_type="offline",
        prompt="consent"
    )

    # Redirect user to Google consent screen and set cookie
    response = RedirectResponse(auth_url)
    response.set_cookie(
        key="google_oauth_code_verifier",
        value=verifier,
        httponly=True,
        max_age=3600,  # 1 hour
        samesite="lax",
        secure=not settings.DEBUG
    )
    return response


@router.get("/google/callback")
async def google_callback(
    request: Request,
    response: Response,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Exchanges the authorization code for tokens, encrypts them at rest,
    and stores them in the google_integrations table for the user.
    """
    if error:
        logger.warning(f"Google OAuth callback error received: {error}")
        raise HTTPException(status_code=400, detail=f"Google OAuth error: {error}")

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing authorization code or state")

    # 1. Verify state and extract user.id
    try:
        user_id_str = verify_oauth_state(state)
        user_uuid = uuid.UUID(user_id_str)
    except Exception as exc:
        logger.warning(f"Google OAuth state verification failed: {exc}")
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    # 2. Get code verifier from cookie
    code_verifier = request.cookies.get("google_oauth_code_verifier")
    if not code_verifier:
        logger.warning("Google OAuth code verifier cookie is missing")
        raise HTTPException(status_code=400, detail="OAuth code verifier cookie is missing")

    # 3. Exchange authorization code
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=None,
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )

    try:
        flow.fetch_token(code=code, code_verifier=code_verifier)
    except Exception as exc:
        logger.exception("Failed to fetch Google OAuth tokens")
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {exc}")

    creds = flow.credentials

    # 4. Encrypt tokens and extract expiry
    try:
        if not creds.token:
            raise HTTPException(status_code=400, detail="No access token received")
        if not creds.expiry:
            raise HTTPException(status_code=400, detail="No token expiry received")
        encrypted_access = encrypt_token(creds.token)
        encrypted_refresh = encrypt_token(creds.refresh_token) if creds.refresh_token else None
        expiry = creds.expiry.replace(tzinfo=timezone.utc)
    except Exception as exc:
        logger.exception("Failed to process Google tokens")
        raise HTTPException(status_code=500, detail="Error securing Google tokens")

    # 5. Upsert google_integrations row
    result = await db.execute(
        select(GoogleIntegration).where(GoogleIntegration.user_id == user_uuid)
    )
    integration = result.scalar_one_or_none()

    if not integration:
        # Check if user exists
        user_result = await db.execute(select(User).where(User.id == user_uuid))
        if not user_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="User not found")

        if not encrypted_refresh:
            raise HTTPException(
                status_code=400,
                detail="Refresh token missing. Please revoke access from your Google Account settings and reconnect."
            )

        integration = GoogleIntegration(
            user_id=user_uuid,
            access_token=encrypted_access,
            refresh_token=encrypted_refresh,
            expires_at=expiry,
            scopes=creds.scopes,
            revoked_at=None
        )
        db.add(integration)
    else:
        integration.access_token = encrypted_access
        if encrypted_refresh:
            integration.refresh_token = encrypted_refresh
        integration.expires_at = expiry
        # Merge scopes
        current_scopes = set(integration.scopes)
        for s in creds.scopes or ():
            current_scopes.add(s)
        integration.scopes = list(current_scopes)
        integration.revoked_at = None

    await db.commit()

    # 6. Delete code verifier cookie
    response_payload = {"status": "connected", "scopes": integration.scopes}
    response_obj = JSONResponse(content=response_payload)
    response_obj.delete_cookie(key="google_oauth_code_verifier")
    return response_obj


@router.get("/google/status")
async def google_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns connection status and authorized scopes.
    """
    result = await db.execute(
        select(GoogleIntegration).where(GoogleIntegration.user_id == user.id)
    )
    integration = result.scalar_one_or_none()

    if not integration or integration.revoked_at is not None:
        return {
            "connected": False,
            "scopes": [],
            "revoked": bool(integration and integration.revoked_at)
        }

    is_expired = integration.expires_at < datetime.now(timezone.utc)

    return {
        "connected": True,
        "scopes": integration.scopes,
        "is_expired": is_expired,
        "revoked": False,
        "expires_at": integration.expires_at.isoformat()
    }


@router.delete("/google")
async def google_disconnect(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Removes the Google integration row for the authenticated user.
    """
    result = await db.execute(
        select(GoogleIntegration).where(GoogleIntegration.user_id == user.id)
    )
    integration = result.scalar_one_or_none()

    if not integration:
        return {"status": "not_connected"}

    await db.delete(integration)
    await db.commit()

    return {"status": "disconnected"}
