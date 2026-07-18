import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from core.deps import get_current_user
from core.exceptions import AuthError, AppError
from models.user import User


@pytest.mark.asyncio
async def test_get_current_user_success():
    # Setup mock request and session
    mock_request = MagicMock(spec=Request)
    mock_db = MagicMock(spec=AsyncSession)

    # Setup expected outputs
    mock_token = "valid_token"
    mock_claims = MagicMock()
    mock_claims.user_id = "clerk_123"

    user_id = uuid.uuid4()
    mock_user = User(
        id=user_id,
        clerk_user_id="clerk_123",
        email="test@example.com"
    )

    # Mock execute result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch("core.deps.extract_bearer_token", return_value=mock_token) as mock_extract, \
         patch("core.deps.verify_clerk_session", return_value=mock_claims) as mock_verify, \
         patch("core.deps.set_user_id") as mock_set_user:
        
        result = await get_current_user(mock_request, mock_db)

        # Assertions
        mock_extract.assert_called_once_with(mock_request)
        mock_verify.assert_called_once_with(mock_token)
        mock_db.execute.assert_called_once()
        mock_set_user.assert_called_once_with(str(user_id))
        assert result == mock_user


@pytest.mark.asyncio
async def test_get_current_user_missing_bearer_token():
    mock_request = MagicMock(spec=Request)
    mock_db = MagicMock(spec=AsyncSession)

    with patch("core.deps.extract_bearer_token", side_effect=AuthError("Missing or malformed Authorization header")):
        with pytest.raises(AuthError) as exc_info:
            await get_current_user(mock_request, mock_db)
        
        assert "Missing or malformed Authorization header" in exc_info.value.message


@pytest.mark.asyncio
async def test_get_current_user_invalid_clerk_session():
    mock_request = MagicMock(spec=Request)
    mock_db = MagicMock(spec=AsyncSession)

    with patch("core.deps.extract_bearer_token", return_value="invalid_token"), \
         patch("core.deps.verify_clerk_session", side_effect=AuthError("Invalid session token")):
        
        with pytest.raises(AuthError) as exc_info:
            await get_current_user(mock_request, mock_db)
        
        assert "Invalid session token" in exc_info.value.message


@pytest.mark.asyncio
async def test_get_current_user_not_synced():
    mock_request = MagicMock(spec=Request)
    mock_db = MagicMock(spec=AsyncSession)

    mock_claims = MagicMock()
    mock_claims.user_id = "clerk_unknown"

    # Mock DB query to return None (user not found)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch("core.deps.extract_bearer_token", return_value="valid_token"), \
         patch("core.deps.verify_clerk_session", return_value=mock_claims):
        
        with pytest.raises(AuthError) as exc_info:
            await get_current_user(mock_request, mock_db)
        
        assert "User not yet synced" in exc_info.value.message


@pytest.mark.asyncio
async def test_get_current_user_database_error():
    mock_request = MagicMock(spec=Request)
    mock_db = MagicMock(spec=AsyncSession)

    mock_claims = MagicMock()
    mock_claims.user_id = "clerk_123"

    # Mock DB query to raise SQLAlchemyError
    mock_db.execute = AsyncMock(side_effect=SQLAlchemyError("Connection timeout"))

    with patch("core.deps.extract_bearer_token", return_value="valid_token"), \
         patch("core.deps.verify_clerk_session", return_value=mock_claims):
        
        with pytest.raises(AppError) as exc_info:
            await get_current_user(mock_request, mock_db)
        
        assert "Database error during user authentication" in exc_info.value.message
        assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_get_current_user_unexpected_exception():
    mock_request = MagicMock(spec=Request)
    mock_db = MagicMock(spec=AsyncSession)

    mock_claims = MagicMock()
    mock_claims.user_id = "clerk_123"

    # Mock DB query to raise an unexpected generic Exception
    mock_db.execute = AsyncMock(side_effect=RuntimeError("Unexpected system failure"))

    with patch("core.deps.extract_bearer_token", return_value="valid_token"), \
         patch("core.deps.verify_clerk_session", return_value=mock_claims):
        
        with pytest.raises(AppError) as exc_info:
            await get_current_user(mock_request, mock_db)
        
        assert "Unexpected authentication database lookup error" in exc_info.value.message
        assert exc_info.value.status_code == 500
