# core/deps.py
"""
FastAPI dependencies that every protected router imports.
get_current_user() is the single place "is this request authenticated" is decided.
"""

import logging
from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from core.security import verify_clerk_session, extract_bearer_token
from core.exceptions import AuthError, AppError
from core.logging import set_user_id
from db.session import get_db
from models.user import User, UserRole

logger = logging.getLogger("core.deps")


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency that extracts the Clerk session token, verifies it against
    Clerk's JWKS, and retrieves the corresponding User ORM object from the database.

    Args:
        request: The incoming FastAPI Request object containing headers.
        db: The async database session dependency.

    Returns:
        User: The authenticated SQLAlchemy User ORM object.

    Raises:
        AuthError: If the token is missing, invalid, expired, or if the user is not found.
        AppError: For database-related issues or unexpected runtime exceptions.
    """
    # 1. Extract Bearer token
    try:
        token = extract_bearer_token(request)
        
        # Developer local-testing bypass
        from core.config import settings
        if settings.APP_ENV == "development" and token.startswith("dev-token-"):
            import uuid
            email = token.removeprefix("dev-token-").strip()
            
            # Check database for existing dev user
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            if not user:
                # Auto-create the dev user to avoid 404
                user = User(
                    id=uuid.uuid4(),
                    clerk_user_id=f"clerk_dev_{email.split('@')[0]}",
                    email=email,
                    role=UserRole.MEMBER
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
                logger.info(f"Auto-created dev user '{email}' with ID '{user.id}'")
            
            set_user_id(str(user.id))
            return user

    except AuthError as exc:
        logger.warning(f"Authentication token extraction failed: {exc.message}")
        raise exc
    except Exception as exc:
        logger.exception("Unexpected error extracting bearer token")
        raise AuthError(f"Invalid authentication header format: {str(exc)}")

    # 2. Verify Clerk session
    try:
        claims = verify_clerk_session(token)
    except AuthError as exc:
        logger.warning(f"Clerk session verification failed: {exc.message}")
        raise exc
    except Exception as exc:
        logger.exception("Unexpected error verifying Clerk session")
        raise AuthError(f"Clerk session validation failed: {str(exc)}")

    # 3. Query the local user
    try:
        result = await db.execute(
            select(User).where(User.clerk_user_id == claims.user_id)
        )
        user = result.scalar_one_or_none()
    except SQLAlchemyError as exc:
        logger.exception("Database error querying user from clerk_user_id")
        raise AppError(f"Database error during user authentication: {str(exc)}")
    except Exception as exc:
        logger.exception("Unexpected error checking database for user")
        raise AppError(f"Unexpected authentication database lookup error: {str(exc)}")

    # 4. Handle non-existent user
    if user is None:
        logger.warning(f"Clerk user ID '{claims.user_id}' not found in local database")
        raise AuthError("User not yet synced — please retry shortly")

    # 5. Populate logging context for downstream tracing
    set_user_id(str(user.id))

    return user


def require_role(*allowed_roles: UserRole):
    """
    Usage: Depends(require_role(UserRole.OWNER, UserRole.ADMIN))
    """
    async def _check(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise AuthError(f"Requires one of roles: {[r.value for r in allowed_roles]}")
        return user

    return _check