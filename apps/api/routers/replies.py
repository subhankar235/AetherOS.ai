import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user
from core.exceptions import ApprovalRequiredError, NotFoundError
from db.session import get_db
from models.draft import Draft
from models.user import User
from agents.reply_agent.drafter import generate_draft
from agents.reply_agent.editor import edit_draft, discard_draft
from agents.reply_agent.sender import prepare_send, execute_send

logger = logging.getLogger("routers.replies")

router = APIRouter(prefix="/replies", tags=["replies"])


class GenerateDraftRequest(BaseModel):
    email_id: uuid.UUID
    instructions: Optional[str] = None


class EditDraftRequest(BaseModel):
    instructions: str
    current_body: Optional[str] = None


class PrepareSendRequest(BaseModel):
    current_body: Optional[str] = None


class SendDraftRequest(BaseModel):
    approval_id: uuid.UUID


@router.post("/drafts")
async def create_reply_draft(
    req: GenerateDraftRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        draft = await generate_draft(
            user_id=user.id,
            email_id=req.email_id,
            instructions=req.instructions,
            db=db,
        )
        return {
            "draft_id": str(draft.id),
            "email_id": str(draft.email_id),
            "body": draft.current_body,
            "version_history": draft.version_history,
            "status": draft.status,
        }
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Failed to generate draft")
        raise HTTPException(status_code=500, detail=f"Failed to generate draft: {str(e)}")


@router.get("/drafts")
async def list_drafts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from models.email_metadata import EmailMetadata
    result = await db.execute(
        select(Draft)
        .where(Draft.user_id == user.id, Draft.status == "drafting")
        .order_by(desc(Draft.created_at))
    )
    drafts = result.scalars().all()
    if not drafts:
        res2 = await db.execute(
            select(Draft).where(Draft.status == "drafting").order_by(desc(Draft.created_at))
        )
        drafts = res2.scalars().all()
    
    output = []
    for d in drafts:
        email_meta = None
        if d.email_id:
            em_res = await db.execute(select(EmailMetadata).where(EmailMetadata.id == d.email_id))
            email_meta = em_res.scalar_one_or_none()

        output.append({
            "id": str(d.id),
            "email_id": str(d.email_id) if d.email_id else None,
            "body": d.current_body,
            "version_history": d.version_history,
            "status": d.status,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "recipient": email_meta.sender if email_meta else None,
            "subject": email_meta.subject if email_meta else None,
            "original_body": email_meta.summary if email_meta else None,
            "original_received_at": email_meta.received_at.isoformat() if email_meta and email_meta.received_at else None,
        })
    return output


@router.post("/drafts/{draft_id}/edit")
async def edit_reply_draft(
    draft_id: uuid.UUID,
    req: EditDraftRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        updated = await edit_draft(
            draft_id=draft_id,
            user_id=user.id,
            instructions=req.instructions,
            db=db,
            current_body_override=req.current_body,
        )
        return {
            "draft_id": str(updated.id),
            "body": updated.current_body,
            "version_history": updated.version_history,
            "status": updated.status,
        }
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to edit draft {draft_id}")
        raise HTTPException(status_code=500, detail=f"Failed to edit draft: {str(e)}")


@router.post("/drafts/{draft_id}/prepare-send")
async def prepare_draft_send(
    draft_id: uuid.UUID,
    req: Optional[PrepareSendRequest] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        current_body = req.current_body if req else None
        prep = await prepare_send(draft_id=draft_id, user_id=user.id, db=db, current_body_override=current_body)
        return prep
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to prepare send for draft {draft_id}")
        raise HTTPException(status_code=500, detail=f"Failed to prepare send: {str(e)}")


@router.post("/drafts/{draft_id}/send")
async def execute_draft_send(
    draft_id: uuid.UUID,
    req: SendDraftRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        from services.approval.approval_gate import approve
        await approve(db, req.approval_id, approved_by=user.email or str(user.id))
        sent = await execute_send(
            draft_id=draft_id,
            approval_id=req.approval_id,
            user=user,
            db=db,
        )
        return sent
    except ApprovalRequiredError as e:
        raise HTTPException(status_code=403, detail=f"Approval required: {str(e)}")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to execute send for draft {draft_id}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


@router.delete("/drafts/{draft_id}")
async def discard_reply_draft(
    draft_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await discard_draft(draft_id=draft_id, user_id=user.id, db=db)
        return {"status": "discarded", "draft_id": str(draft_id)}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to discard draft {draft_id}")
        raise HTTPException(status_code=500, detail=f"Failed to discard draft: {str(e)}")
