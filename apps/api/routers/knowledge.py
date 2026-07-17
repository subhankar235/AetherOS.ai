import logging
import os
import shutil
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.deps import get_current_user
from core.exceptions import NotFoundError, ValidationError, AuthError
from db.session import get_db
from integrations.qdrant_client import qdrant_client
from models.knowledge_document import KnowledgeDocument
from models.user import User, UserRole
from schemas.knowledge_document_schema import (
    KnowledgeDocumentResponse,
    KnowledgeDocumentUpdate,
)
from services.rag.embedder import embedder_service
from workers.kb_indexer import index_document_task

logger = logging.getLogger("routers.knowledge")

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

UPLOADS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))


def _get_allowed_roles(role: UserRole) -> List[str]:
    """
    Returns database access_level strings accessible by the given user role.
    """
    if role == UserRole.OWNER:
        return ["Owner", "Admin", "Member", "Viewer"]
    elif role == UserRole.ADMIN:
        return ["Admin", "Member", "Viewer"]
    elif role == UserRole.MEMBER:
        return ["Member", "Viewer"]
    else:  # Viewer or unknown
        return ["Viewer"]


async def _resolve_org_id(request: Request, form_org_id: Optional[str] = None) -> str:
    """
    Resolves the organization ID for the request.
    First checks the form argument, then tries Clerk JWT claims, and defaults to 'default_org'.
    """
    if form_org_id:
        return form_org_id

    # Fallback: Parse from Clerk JWT claims if available
    try:
        from core.security import extract_bearer_token, verify_clerk_session
        token = extract_bearer_token(request)
        claims = verify_clerk_session(token)
        org_id = claims.raw.get("org_id")
        if org_id:
            return org_id
    except Exception:
        pass

    return "default_org"


async def _set_db_rls_context(db: AsyncSession, org_id: str) -> None:
    """
    Sets the database session variable app.current_org_id to comply with Postgres RLS.
    """
    try:
        await db.execute(
            text("SELECT set_config('app.current_org_id', :org_id, True)"),
            {"org_id": org_id}
        )
    except Exception as e:
        logger.error(f"Failed to set database RLS organization ID context: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal database session setup failed")


@router.post("/upload", response_model=KnowledgeDocumentResponse)
async def upload_document(
    request: Request,
    title: str = Form(...),
    access_level: str = Form("Member"),
    org_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Uploads a document file, saves it to disk, creates a queued record in the database
    (setting Postgres RLS context), and schedules a Celery background indexing task.
    """
    resolved_org = await _resolve_org_id(request, org_id)

    # Validate access level
    if access_level not in ["Owner", "Admin", "Member", "Viewer"]:
        raise HTTPException(status_code=400, detail="Invalid access_level value")

    # Ensure uploads directory exists
    os.makedirs(UPLOADS_DIR, exist_ok=True)

    # Save uploaded file
    doc_id = uuid.uuid4()
    _, ext = os.path.splitext(file.filename)
    safe_filename = f"{doc_id}{ext}"
    dest_path = os.path.join(UPLOADS_DIR, safe_filename)

    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to write uploaded file to disk: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")

    # Set Postgres RLS session org
    await _set_db_rls_context(db, resolved_org)

    # Write to database
    try:
        doc = KnowledgeDocument(
            id=doc_id,
            org_id=resolved_org,
            user_id=user.id,
            title=title,
            source_type="upload",
            file_path_or_url=dest_path,
            doc_type=ext.lstrip(".").lower(),
            access_level=access_level,
            indexing_status="queued",
            uploaded_by=user.id,
            created_at=datetime.now(timezone.utc)
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        logger.info(f"Created knowledge document record '{doc_id}' for org '{resolved_org}'")
    except Exception as e:
        logger.exception(f"Failed to create document record in Postgres: {str(e)}")
        # Clean up file
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise HTTPException(status_code=500, detail="Failed to create document record")

    # Trigger background indexing Celery task
    try:
        index_document_task.delay(str(doc_id))
        logger.info(f"Enqueued indexing Celery job for document '{doc_id}'")
    except Exception as e:
        logger.exception(f"Failed to enqueue Celery indexing task: {str(e)}")
        # We do not fail the request since the DB entry is successfully saved as queued

    return doc


@router.get("/documents", response_model=List[KnowledgeDocumentResponse])
async def list_documents(
    request: Request,
    org_id: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists all knowledge base documents for the user's organization,
    subject to RLS and access level filtering.
    """
    resolved_org = await _resolve_org_id(request, org_id)

    # Set Postgres RLS session org
    await _set_db_rls_context(db, resolved_org)

    # Filter documents by access levels matching the user's role hierarchy
    allowed_levels = _get_allowed_roles(user.role)
    try:
        result = await db.execute(
            select(KnowledgeDocument)
            .where(KnowledgeDocument.org_id == resolved_org)
            .where(KnowledgeDocument.access_level.in_(allowed_levels))
            .order_by(KnowledgeDocument.created_at.desc())
        )
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Failed to query knowledge documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve documents")


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: uuid.UUID,
    request: Request,
    org_id: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Deletes a document from the database (respecting RLS), deletes its vector chunks
    from Qdrant, and removes the local file from disk.
    """
    resolved_org = await _resolve_org_id(request, org_id)

    # Set Postgres RLS session org
    await _set_db_rls_context(db, resolved_org)

    # Query the document
    result = await db.execute(
        select(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or access denied")

    # 1. Delete local file
    file_path = doc.file_path_or_url
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            logger.info(f"Removed file from disk: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to remove file '{file_path}' from disk: {str(e)}")

    # 2. Delete points from Qdrant vector store
    try:
        # Document chunks are identified deterministically using UUIDv5 based on document UUID
        # Since we don't know the exact count of chunks, we can query or delete by chunks loop.
        # Alternatively, we can construct the list of IDs if we know they are structured as chunk_0, chunk_1 etc.
        # We can also search in Qdrant for points where payload['doc_id'] == document_id, but Qdrant's delete
        # has selector parameters.
        # Let's delete using a payload filter selector in Qdrant client!
        client = qdrant_client.get_client()
        from qdrant_client.http import models as qdrant_models
        await client.delete(
            collection_name=settings.QDRANT_COLLECTION_COMPANY_MEMORY,
            points_selector=qdrant_models.FilterSelector(
                filter=qdrant_models.Filter(
                    must=[
                        qdrant_models.FieldCondition(
                            key="doc_id",
                            match=qdrant_models.MatchValue(value=str(document_id))
                        )
                    ]
                )
            )
        )
        logger.info(f"Deleted vector chunks for document '{document_id}' from Qdrant")
    except Exception as e:
        logger.error(f"Failed to delete vectors from Qdrant for document '{document_id}': {str(e)}")

    # 3. Delete DB record
    try:
        await db.delete(doc)
        await db.commit()
        logger.info(f"Deleted database record for document '{document_id}'")
    except Exception as e:
        logger.error(f"Failed to delete database record: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete document database record")

    return {"detail": "Document successfully deleted"}


@router.post("/query")
async def query_knowledge(
    request: Request,
    query: str = Form(...),
    limit: int = Form(5),
    org_id: Optional[str] = Form(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Direct semantic query search on knowledge base.
    Generates embedding for query, and runs access-controlled search on Qdrant.
    """
    resolved_org = await _resolve_org_id(request, org_id)

    # 1. Embed query text
    try:
        embeddings = await embedder_service.embed_chunks([query])
        query_vector = embeddings[0]
    except Exception as e:
        logger.error(f"Failed to generate embedding for query: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process search query text")

    # 2. Search Qdrant
    try:
        # Access level uses user.role (normalized string format)
        results = await qdrant_client.search(
            collection_name=settings.QDRANT_COLLECTION_COMPANY_MEMORY,
            query_vector=query_vector,
            org_id=resolved_org,
            access_level=user.role.value,
            limit=limit
        )
        
        # Format scored points into serializable format
        return [
            {
                "score": scored_point.score,
                "payload": scored_point.payload
            }
            for scored_point in results
        ]
    except Exception as e:
        logger.error(f"Search query against Qdrant failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to run semantic query search")
