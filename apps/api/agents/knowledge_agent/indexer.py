import logging
import uuid
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import NotFoundError, ValidationError
from models.knowledge_document import KnowledgeDocument
from workers.kb_indexer import index_document_task

logger = logging.getLogger("agents.knowledge_agent.indexer")


async def trigger_indexing(
    document_id: str,
    db: AsyncSession,
) -> dict[str, Any]:
    doc_uuid = _validate_document_id(document_id)

    doc = await _fetch_document(doc_uuid, db)
    if doc is None:
        raise NotFoundError(f"Document '{document_id}' not found")

    if doc.indexing_status == "ready":
        return {
            "doc_id": document_id,
            "title": doc.title,
            "indexing_status": "ready",
            "message": "Document is already indexed. Re-indexing triggered.",
        }

    if doc.indexing_status == "processing":
        return {
            "doc_id": document_id,
            "title": doc.title,
            "indexing_status": "processing",
            "message": "Document is currently being indexed. Please wait.",
        }

    try:
        index_document_task.delay(document_id)
        logger.info(f"Re-indexing enqueued for document '{document_id}'")
    except Exception as exc:
        logger.exception(f"Failed to enqueue indexing for document '{document_id}': {exc}")
        raise

    return {
        "doc_id": document_id,
        "title": doc.title,
        "indexing_status": "queued",
        "message": "Indexing job has been enqueued.",
    }


def _validate_document_id(document_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(document_id)
    except ValueError:
        raise ValidationError(f"Invalid document ID format: '{document_id}'")


async def _fetch_document(
    doc_uuid: uuid.UUID,
    db: AsyncSession,
) -> Optional[KnowledgeDocument]:
    try:
        result = await db.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.id == doc_uuid)
        )
        return result.scalar_one_or_none()
    except Exception as exc:
        logger.exception(f"Failed to query document '{doc_uuid}': {exc}")
        raise


async def check_indexing_status(
    document_id: str,
    db: AsyncSession,
) -> dict[str, Any]:
    doc_uuid = _validate_document_id(document_id)
    doc = await _fetch_document(doc_uuid, db)

    if doc is None:
        raise NotFoundError(f"Document '{document_id}' not found")

    return {
        "doc_id": document_id,
        "title": doc.title,
        "indexing_status": doc.indexing_status,
        "created_at": doc.created_at.isoformat() if doc.created_at else "",
    }
