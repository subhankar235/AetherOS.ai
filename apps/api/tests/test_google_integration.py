import uuid
from datetime import datetime, timezone, timedelta
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials

from main import app
from core.config import settings
from core.deps import get_current_user
from db.session import get_db
from core.exceptions import AuthError, AppError, IntegrationAuthRequiredError, RateLimitError
from core.security import encrypt_token, decrypt_token, generate_oauth_state, verify_oauth_state
from models.user import User
from models.google_integration import GoogleIntegration
from integrations.google_auth import (
    GoogleScopes,
    check_scopes_granted,
    refresh_google_credentials,
    get_google_credentials,
)
from integrations.gmail_client import (
    fetch_message,
    search_messages,
    send_message,
    create_draft,
    list_labels,
    get_thread,
    watch_inbox,
)
from integrations.calendar_client import (
    get_freebusy,
    create_event,
    update_event,
    delete_event,
)
from integrations.meet_client import generate_meet_conference_data

client = TestClient(app)

# Setup a global mock user
mock_user_id = uuid.uuid4()
mock_user = User(
    id=mock_user_id,
    clerk_user_id="clerk_123",
    email="test@example.com"
)

# Global mock database session
mock_db = AsyncMock(spec=AsyncSession)


@pytest.fixture(autouse=True)
def override_dependencies():
    """
    Override dependencies globally for route tests.
    """
    async def _get_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.clear()
    mock_db.reset_mock()


# --- 1. Security & Cryptography Tests --------------------------------------

def test_encryption_decryption():
    original_token = "ya29.a0AfH6SMA..."
    encrypted = encrypt_token(original_token)
    assert encrypted != original_token
    
    decrypted = decrypt_token(encrypted)
    assert decrypted == original_token


def test_oauth_state_signing():
    user_id = str(uuid.uuid4())
    state = generate_oauth_state(user_id)
    assert state != user_id
    
    verified_user_id = verify_oauth_state(state)
    assert verified_user_id == user_id


def test_invalid_oauth_state():
    with pytest.raises(AuthError):
        verify_oauth_state("invalid-signed-state")


# --- 2. Google OAuth Credentials & Refresh Tests --------------------------

@pytest.mark.asyncio
async def test_check_scopes_granted():
    integration = GoogleIntegration(
        scopes=GoogleScopes.BASE
    )
    assert check_scopes_granted(integration, [GoogleScopes.BASE[3]])
    assert not check_scopes_granted(integration, [GoogleScopes.CALENDAR])


@pytest.mark.asyncio
async def test_refresh_google_credentials_not_expired():
    expiry = datetime.now(timezone.utc) + timedelta(hours=1)
    integration = GoogleIntegration(
        user_id=uuid.uuid4(),
        access_token=encrypt_token("access_123"),
        refresh_token=encrypt_token("refresh_123"),
        expires_at=expiry,
        scopes=GoogleScopes.BASE
    )
    
    with patch("integrations.google_auth.Credentials") as mock_creds_class:
        mock_creds = MagicMock(spec=Credentials)
        mock_creds.expired = False
        mock_creds_class.return_value = mock_creds
        
        creds = await refresh_google_credentials(mock_db, integration)
        assert creds == mock_creds
        mock_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_refresh_google_credentials_expired_success():
    expiry = datetime.now(timezone.utc) - timedelta(hours=1)
    integration = GoogleIntegration(
        user_id=uuid.uuid4(),
        access_token=encrypt_token("access_old"),
        refresh_token=encrypt_token("refresh_123"),
        expires_at=expiry,
        scopes=GoogleScopes.BASE
    )
    
    with patch("integrations.google_auth.Credentials") as mock_creds_class, \
         patch("integrations.google_auth.GoogleRequest") as mock_req_class:
        
        mock_creds = MagicMock(spec=Credentials)
        mock_creds.expired = True
        mock_creds.token = "access_new"
        mock_creds.refresh_token = "refresh_123"
        mock_creds.expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_creds_class.return_value = mock_creds
        
        creds = await refresh_google_credentials(mock_db, integration)
        assert creds == mock_creds
        mock_creds.refresh.assert_called_once()
        mock_db.commit.assert_called_once()
        assert decrypt_token(integration.access_token) == "access_new"


@pytest.mark.asyncio
async def test_refresh_google_credentials_revoked():
    expiry = datetime.now(timezone.utc) - timedelta(hours=1)
    integration = GoogleIntegration(
        user_id=uuid.uuid4(),
        access_token=encrypt_token("access_old"),
        refresh_token=encrypt_token("refresh_123"),
        expires_at=expiry,
        scopes=GoogleScopes.BASE
    )
    
    with patch("integrations.google_auth.Credentials") as mock_creds_class, \
         patch("integrations.google_auth.GoogleRequest") as mock_req_class:
        
        mock_creds = MagicMock(spec=Credentials)
        mock_creds.expired = True
        mock_creds.refresh.side_effect = RefreshError("Token revoked")
        mock_creds_class.return_value = mock_creds
        
        with pytest.raises(IntegrationAuthRequiredError):
            await refresh_google_credentials(mock_db, integration)
            
        assert integration.revoked_at is not None
        mock_db.commit.assert_called_once()


# --- 3. Endpoints (Mocking User and DB) ------------------------------------

def test_google_connect():
    response = client.get("/integrations/google/connect", follow_redirects=False)
    assert response.status_code == 307
    assert "accounts.google.com" in response.headers["location"]
    assert "google_oauth_code_verifier" in response.cookies


def test_google_callback_success():
    state = generate_oauth_state(str(mock_user.id))
    
    # Return user when queried by UUID
    mock_result_user = MagicMock()
    mock_result_user.scalar_one_or_none.return_value = mock_user
    
    # Return no existing integration when queried
    mock_result_integration = MagicMock()
    mock_result_integration.scalar_one_or_none.return_value = None
    
    mock_db.execute.side_effect = [mock_result_integration, mock_result_user]
    
    with patch("routers.integrations.Flow") as mock_flow_class:
        mock_flow = MagicMock()
        mock_flow.credentials.token = "access_123"
        mock_flow.credentials.refresh_token = "refresh_123"
        mock_flow.credentials.expiry = datetime.now(timezone.utc)
        mock_flow.credentials.scopes = GoogleScopes.BASE
        mock_flow_class.from_client_config.return_value = mock_flow
        
        # Set verifier cookie
        client.cookies.set("google_oauth_code_verifier", "verifier_123")
        
        response = client.get(
            f"/integrations/google/callback?code=code_123&state={state}",
            follow_redirects=False
        )
        
        assert response.status_code == 307
        assert "google=connected" in response.headers["location"]
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


def test_google_status_connected():
    integration = GoogleIntegration(
        user_id=mock_user.id,
        access_token=encrypt_token("access_123"),
        refresh_token=encrypt_token("refresh_123"),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        scopes=GoogleScopes.BASE
    )
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = integration
    mock_db.execute.side_effect = None
    mock_db.execute.return_value = mock_result
    
    response = client.get("/integrations/google/status")
    assert response.status_code == 200
    assert response.json()["connected"] is True
    assert GoogleScopes.BASE[3] in response.json()["scopes"]


def test_google_disconnect():
    integration = GoogleIntegration(
        user_id=mock_user.id,
        access_token="encrypted",
        refresh_token="encrypted",
        expires_at=datetime.now(timezone.utc)
    )
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = integration
    mock_db.execute.side_effect = None
    mock_db.execute.return_value = mock_result
    
    response = client.delete("/integrations/google")
    assert response.status_code == 200
    assert response.json()["status"] == "disconnected"
    mock_db.delete.assert_called_once()
    mock_db.commit.assert_called_once()


# --- 4. Gmail Client Operations --------------------------------------------

@pytest.mark.asyncio
async def test_gmail_fetch_message():
    db = AsyncMock(spec=AsyncSession)
    user_id = uuid.uuid4()
    
    # Mock credentials fetch
    creds = MagicMock(spec=Credentials)
    
    # Mock Google Gmail service
    mock_service = MagicMock()
    mock_get = MagicMock()
    mock_service.users().messages().get.return_value = mock_get
    mock_get.execute.return_value = {"id": "msg_123", "snippet": "Hello World"}
    
    with patch("integrations.gmail_client.get_google_credentials", return_value=creds), \
         patch("integrations.gmail_client.build", return_value=mock_service), \
         patch("integrations.gmail_client.limiter.check_rate_limit") as mock_limiter:
         
        msg = await fetch_message(user_id, "msg_123", db)
        assert msg["id"] == "msg_123"
        mock_limiter.assert_called_once()
        mock_service.users().messages().get.assert_called_once_with(userId="me", id="msg_123", format="full")


# --- 5. Calendar & Meet Client Operations ----------------------------------

@pytest.mark.asyncio
async def test_calendar_create_event():
    db = AsyncMock(spec=AsyncSession)
    user_id = uuid.uuid4()
    
    # Mock credentials fetch
    creds = MagicMock(spec=Credentials)
    
    # Mock Google Calendar service
    mock_service = MagicMock()
    mock_insert = MagicMock()
    mock_service.events().insert.return_value = mock_insert
    mock_insert.execute.return_value = {"id": "evt_123", "htmlLink": "https://calendar/event"}
    
    event_body = {
        "summary": "Quick Meetup",
        "start": {"dateTime": "2026-07-16T22:00:00Z"},
        "end": {"dateTime": "2026-07-16T22:30:00Z"},
        "conferenceData": generate_meet_conference_data()
    }
    
    with patch("integrations.calendar_client.get_google_credentials", return_value=creds), \
         patch("integrations.calendar_client.build", return_value=mock_service), \
         patch("integrations.calendar_client.limiter.check_rate_limit") as mock_limiter:
         
        evt = await create_event(user_id, "primary", event_body, db, conference_data_version=1)
        assert evt["id"] == "evt_123"
        mock_limiter.assert_called_once()
        mock_service.events().insert.assert_called_once_with(
            calendarId="primary",
            body=event_body,
            conferenceDataVersion=1
        )


# --- 6. Gmail Webhook & Celery Task Enqueue ---------------------------------

def test_gmail_webhook_unauthorized():
    response = client.post("/webhooks/gmail?token=bad_token", json={"message": "new_email"})
    assert response.status_code == 401


def test_gmail_webhook_authorized():
    with patch("routers.inbox.process_gmail_notification.delay") as mock_task:
        response = client.post(
            f"/webhooks/gmail?token={settings.GOOGLE_PUBSUB_VERIFICATION_TOKEN}",
            json={"message": {"data": "encoded_payload"}}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "enqueued"
        mock_task.assert_called_once_with({"message": {"data": "encoded_payload"}})
