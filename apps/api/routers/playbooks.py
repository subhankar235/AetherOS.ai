import logging
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user
from db.session import get_db
from models.playbook import Playbook
from models.user import User
from schemas.playbook_schema import PlaybookCreate, PlaybookUpdate, PlaybookResponse

logger = logging.getLogger("routers.playbooks")

router = APIRouter(prefix="/playbooks", tags=["playbooks"])


@router.get("", response_model=list[PlaybookResponse])
async def list_playbooks(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Playbook)
        .where((Playbook.user_id == user.id) | (Playbook.user_id.is_(None)))
        .order_by(desc(Playbook.created_at))
    )
    return result.scalars().all()


@router.get("/{playbook_id}", response_model=PlaybookResponse)
async def get_playbook(
    playbook_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Playbook).where(Playbook.id == playbook_id)
    )
    playbook = result.scalar_one_or_none()
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return playbook


@router.post("", response_model=PlaybookResponse, status_code=201)
async def create_playbook(
    payload: PlaybookCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    playbook = Playbook(
        id=uuid.uuid4(),
        user_id=user.id,
        org_id=payload.org_id,
        name=payload.name,
        scenario_type=payload.scenario_type,
        template_structure=payload.template_structure,
        tone_settings=payload.tone_settings,
    )
    db.add(playbook)
    await db.commit()
    await db.refresh(playbook)
    return playbook


@router.put("/{playbook_id}", response_model=PlaybookResponse)
async def update_playbook(
    playbook_id: uuid.UUID,
    payload: PlaybookUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Playbook).where(Playbook.id == playbook_id)
    )
    playbook = result.scalar_one_or_none()
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(playbook, field, value)

    await db.commit()
    await db.refresh(playbook)
    return playbook


@router.delete("/{playbook_id}")
async def delete_playbook(
    playbook_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Playbook).where(Playbook.id == playbook_id)
    )
    playbook = result.scalar_one_or_none()
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")

    await db.delete(playbook)
    await db.commit()
    return {"detail": "Playbook deleted"}
