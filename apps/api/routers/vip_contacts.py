import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user
from db.session import get_db
from models.vip_contact import VIPContact
from models.user import User
from schemas.vip_contact_schema import VIPContactCreate, VIPContactUpdate, VIPContactResponse

logger = logging.getLogger("routers.vip_contacts")

router = APIRouter(prefix="/vip-contacts", tags=["vip_contacts"])


@router.get("", response_model=list[VIPContactResponse])
async def list_vip_contacts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VIPContact)
        .where(VIPContact.user_id == user.id)
        .order_by(desc(VIPContact.added_at))
    )
    return result.scalars().all()


@router.get("/{contact_id}", response_model=VIPContactResponse)
async def get_vip_contact(
    contact_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VIPContact).where(
            VIPContact.id == contact_id,
            VIPContact.user_id == user.id,
        )
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="VIP contact not found")
    return contact


@router.post("", response_model=VIPContactResponse, status_code=201)
async def create_vip_contact(
    payload: VIPContactCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(VIPContact).where(
            VIPContact.user_id == user.id,
            VIPContact.contact_email == payload.contact_email,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Contact already in VIP list")

    contact = VIPContact(
        id=uuid.uuid4(),
        user_id=user.id,
        contact_email=payload.contact_email,
        contact_name=payload.contact_name,
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


@router.put("/{contact_id}", response_model=VIPContactResponse)
async def update_vip_contact(
    contact_id: uuid.UUID,
    payload: VIPContactUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VIPContact).where(
            VIPContact.id == contact_id,
            VIPContact.user_id == user.id,
        )
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="VIP contact not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contact, field, value)

    await db.commit()
    await db.refresh(contact)
    return contact


@router.delete("/{contact_id}")
async def delete_vip_contact(
    contact_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VIPContact).where(
            VIPContact.id == contact_id,
            VIPContact.user_id == user.id,
        )
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="VIP contact not found")

    await db.delete(contact)
    await db.commit()
    return {"detail": "VIP contact deleted"}
