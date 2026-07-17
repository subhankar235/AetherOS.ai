import asyncio
import logging
import uuid
from datetime import datetime, timezone

from core.celery_app import celery_app
from db.session import AsyncSessionLocal
from models.knowledge_document import KnowledgeDocument
from sqlalchemy import select

logger = logging.getLogger("workers.kb_indexer")


async def _index_document(document_id: str) -> None:
    # Local imports inside function to prevent circular dependency cycles
    from core.config import settings
    from integrations.qdrant_client import qdrant_client
    from qdrant_client.http import models as qdrant_models
    from services.ingestion.chunker import chunk_text
    from services.ingestion.parser import parse_document
    from services.rag.embedder import embedder_service

    doc_uuid = uuid.UUID(document_id)

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(KnowledgeDocument).where(KnowledgeDocument.id == doc_uuid)
            )
            doc = result.scalar_one_or_none()
            if not doc:
                logger.error(f"Document '{document_id}' not found in database.")
                return

            # Update status to processing
            doc.indexing_status = "processing"
            await db.commit()
            await db.refresh(doc)
            logger.info(f"Document '{document_id}' status set to 'processing'")
        except Exception as e:
            logger.exception(f"Failed to fetch document or update status to 'processing': {str(e)}")
            return

        try:
            # Parse text from document path
            text_content = parse_document(file_path=doc.file_path_or_url)
            if not text_content or not text_content.strip():
                raise ValueError("Extracted text from document is empty")

            # Chunk document content
            chunks = chunk_text(text_content)
            if not chunks:
                raise ValueError("No text chunks generated from parsed document")

            # Generate vector embeddings
            embeddings = await embedder_service.embed_chunks(chunks)

            # Build Qdrant points with metadata payload
            points = []
            for idx, (chunk, vector) in enumerate(zip(chunks, embeddings)):
                # Generate a unique deterministic UUID for each chunk point
                point_uuid = str(uuid.uuid5(doc_uuid, f"chunk_{idx}"))
                points.append(
                    qdrant_models.PointStruct(
                        id=point_uuid,
                        vector=vector,
                        payload={
                            "doc_id": str(doc.id),
                            "org_id": doc.org_id,
                            "access_level": doc.access_level,
                            "source": doc.file_path_or_url,
                            "chunk_text": chunk,
                            "upload_date": doc.created_at.isoformat() if doc.created_at else datetime.now(timezone.utc).isoformat()
                        }
                    )
                )

            # Upsert into Qdrant
            await qdrant_client.upsert(
                collection_name=settings.QDRANT_COLLECTION_COMPANY_MEMORY,
                points=points
            )

            # Transition document status to ready
            doc.indexing_status = "ready"
            await db.commit()
            logger.info(f"Document '{document_id}' successfully indexed and status set to 'ready'")

        except Exception as exc:
            logger.exception(f"Error occurred while indexing document '{document_id}': {str(exc)}")
            try:
                # Transition status to failed
                doc.indexing_status = "failed"
                await db.commit()
                logger.info(f"Document '{document_id}' status set to 'failed'")
            except Exception as commit_err:
                logger.exception(f"Failed to commit 'failed' status for document '{document_id}': {str(commit_err)}")


@celery_app.task(name="workers.kb_indexer.index_document_task")
def index_document_task(document_id: str) -> None:
    """
    Celery background task to orchestrate document parsing, chunking, embedding,
    and storage in Qdrant. Tracks indexing status transitions.
    """
    logger.info(f"Triggered index_document_task Celery task for document ID: {document_id}")
    
    coro = _index_document(document_id)
    
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import threading
        import queue

        q = queue.Queue()

        def run_in_thread():
            try:
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                res = new_loop.run_until_complete(coro)
                q.put((True, res))
            except Exception as e:
                q.put((False, e))
            finally:
                new_loop.close()

        t = threading.Thread(target=run_in_thread)
        t.start()
        t.join()

        success, val = q.get()
        if not success:
            raise val
    else:
        asyncio.run(coro)
