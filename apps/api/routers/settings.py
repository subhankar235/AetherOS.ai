import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user
from db.session import get_db
from models.user import User
from schemas.user_schema import UserUpdate, UserResponse

logger = logging.getLogger("routers.settings")

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/profile", response_model=UserResponse)
async def get_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return user


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    payload: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(user, field):
            setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user


@router.get("/preferences")
async def get_preferences(
    user: User = Depends(get_current_user),
):
    return {
        "timezone": user.timezone,
        "language": user.language_preference,
        "plan_tier": user.plan_tier,
        "voice_history_opt_in": user.voice_history_opt_in,
    }


@router.put("/preferences")
async def update_preferences(
    timezone: Optional[str] = None,
    language: Optional[str] = None,
    voice_history_opt_in: Optional[bool] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if timezone is not None:
        user.timezone = timezone
    if language is not None:
        user.language_preference = language
    if voice_history_opt_in is not None:
        user.voice_history_opt_in = voice_history_opt_in

    await db.commit()
    await db.refresh(user)

    return {
        "timezone": user.timezone,
        "language": user.language_preference,
        "plan_tier": user.plan_tier,
        "voice_history_opt_in": user.voice_history_opt_in,
    }
