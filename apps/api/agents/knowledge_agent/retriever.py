import logging
import uuid
from typing import Any, Optional

from langchain_openai import ChatOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.exceptions import ExternalServiceError
from integrations.qdrant_client import qdrant_client
from models.knowledge_document import KnowledgeDocument
from services.rag.embedder import embedder_service
from agents.supervisor.prompts import INJECTION_GUARDRAIL

logger = logging.getLogger("agents.knowledge_agent.retriever")

RE_RANK_PROMPT = """You are a relevance re-ranker for a knowledge base retrieval system.

Given a user query and a set of candidate text passages, your job is to:
1. Score each passage on relevance to the query (0-10)
2. Identify whether any passages contain conflicting information
3. Produce a synthesized answer that accurately reflects the retrieved information

Rules:
- Only use information present in the provided passages — do not add external knowledge
- If passages contain conflicting information, surface both sides with their sources
- If no passage is relevant, say "No relevant information found in knowledge base"
- Cite the source document title for each claim

""" + INJECTION_GUARDRAIL


async def query_knowledge(
    query: str,
    user_id: uuid.UUID,
    org_id: str,
    access_level: str,
    db: AsyncSession,
    limit: int = 5,
    llm: Optional[ChatOpenAI] = None,
) -> dict[str, Any]:
    if llm is None:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=settings.OPENAI_API_KEY,
        )

    query_vector = await _embed_query(query)

    scored_points = await _search_qdrant(query_vector, org_id, access_level, limit)

    if not scored_points:
        return _not_found_result(query)

    chunk_texts, source_map = _extract_chunks_with_sources(scored_points)

    logger.info(
        f"Retrieved {len(chunk_texts)} chunks from "
        f"{len(set(s.get('doc_id') for s in source_map.values()))} documents "
        f"for query: '{query[:80]}...'"
    )

    doc_metadata = await _fetch_doc_metadata(list(source_map.values()), db)

    conflicts = _detect_conflicts(scored_points, source_map, doc_metadata)

    answer = await _synthesize_answer(query, chunk_texts, source_map, doc_metadata, llm)

    sources = _build_sources(source_map, doc_metadata)

    return {
        "agent": "knowledge_agent",
        "status": "completed",
        "result": {
            "answer": answer,
            "sources": sources,
            "conflicts_detected": len(conflicts) > 0,
            "conflicts": conflicts,
            "total_results": len(scored_points),
        },
        "context_updates": {"last_knowledge_query": query},
        "requires_approval": False,
    }


async def _embed_query(query: str) -> list[float]:
    try:
        embeddings = await embedder_service.embed_chunks([query])
        return embeddings[0]
    except Exception as exc:
        logger.exception(f"Failed to embed query: {exc}")
        raise ExternalServiceError(f"Failed to generate query embedding: {str(exc)}")


async def _search_qdrant(
    query_vector: list[float],
    org_id: str,
    access_level: str,
    limit: int,
) -> list[Any]:
    try:
        return await qdrant_client.search(
            collection_name=settings.QDRANT_COLLECTION_COMPANY_MEMORY,
            query_vector=query_vector,
            org_id=org_id,
            access_level=access_level,
            limit=limit,
        )
    except Exception as exc:
        logger.exception(f"Qdrant search failed: {exc}")
        raise ExternalServiceError(f"Knowledge base search failed: {str(exc)}")


def _extract_chunks_with_sources(
    scored_points: list[Any],
) -> tuple[list[str], dict[int, dict[str, str]]]:
    chunk_texts = []
    source_map: dict[int, dict[str, str]] = {}

    for i, pt in enumerate(scored_points):
        payload = pt.payload or {}
        chunk_texts.append(payload.get("chunk_text", ""))
        source_map[i] = {
            "doc_id": payload.get("doc_id", ""),
            "score": str(round(pt.score, 4)),
            "source": payload.get("source", ""),
            "upload_date": payload.get("upload_date", ""),
        }

    return chunk_texts, source_map


async def _fetch_doc_metadata(
    source_entries: list[dict[str, str]],
    db: AsyncSession,
) -> dict[str, dict[str, Any]]:
    doc_ids = set()
    for entry in source_entries:
        did = entry.get("doc_id", "")
        if did:
            try:
                doc_ids.add(uuid.UUID(did))
            except ValueError:
                pass

    if not doc_ids:
        return {}

    try:
        result = await db.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.id.in_(list(doc_ids)))
        )
        docs = result.scalars().all()
        return {
            str(d.id): {
                "title": d.title,
                "doc_type": d.doc_type,
                "created_at": d.created_at.isoformat() if d.created_at else "",
                "access_level": d.access_level,
                "indexing_status": d.indexing_status,
            }
            for d in docs
        }
    except Exception as exc:
        logger.warning(f"Failed to fetch document metadata: {exc}")
        return {}


def _detect_conflicts(
    scored_points: list[Any],
    source_map: dict[int, dict[str, str]],
    doc_metadata: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    doc_groups: dict[str, list[dict[str, Any]]] = {}
    for i, pt in enumerate(scored_points):
        payload = pt.payload or {}
        did = payload.get("doc_id", "")
        if did not in doc_groups:
            doc_groups[did] = []
        doc_groups[did].append({
            "index": i,
            "text": payload.get("chunk_text", "")[:200],
            "score": pt.score,
        })

    doc_ids = list(doc_groups.keys())
    conflicts = []

    for i in range(len(doc_ids)):
        for j in range(i + 1, len(doc_ids)):
            id_a, id_b = doc_ids[i], doc_ids[j]
            meta_a = doc_metadata.get(id_a, {})
            meta_b = doc_metadata.get(id_b, {})

            title_a = meta_a.get("title", "Unknown")
            title_b = meta_b.get("title", "Unknown")
            date_a = meta_a.get("created_at", "")
            date_b = meta_b.get("created_at", "")

            if id_a != id_b:
                conflicts.append({
                    "type": "multiple_sources",
                    "message": f"Information retrieved from multiple documents: '{title_a}' and '{title_b}'",
                    "sources": [
                        {"doc_id": id_a, "title": title_a, "date": date_a},
                        {"doc_id": id_b, "title": title_b, "date": date_b},
                    ],
                    "detail": "Both sources are shown below. Verify which is the latest or most authoritative.",
                })

    return conflicts


def _build_sources(
    source_map: dict[int, dict[str, str]],
    doc_metadata: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    seen: set[str] = set()
    sources = []
    for i in sorted(source_map.keys()):
        entry = source_map[i]
        did = entry.get("doc_id", "")
        if did in seen:
            continue
        seen.add(did)
        meta = doc_metadata.get(did, {})
        sources.append({
            "doc_id": did,
            "title": meta.get("title", "Unknown"),
            "doc_type": meta.get("doc_type", ""),
            "date": meta.get("created_at", entry.get("upload_date", "")),
            "relevance_score": entry.get("score", ""),
        })
    return sources


async def _synthesize_answer(
    query: str,
    chunk_texts: list[str],
    source_map: dict[int, dict[str, str]],
    doc_metadata: dict[str, dict[str, Any]],
    llm: ChatOpenAI,
) -> str:
    passages = []
    for i, text in enumerate(chunk_texts):
        entry = source_map.get(i, {})
        did = entry.get("doc_id", "")
        meta = doc_metadata.get(did, {})
        title = meta.get("title", "Unknown")
        passages.append(f"[Passage {i + 1}] Source: '{title}'\n{text[:2000]}")

    combined = "\n\n---\n\n".join(passages)

    try:
        response = await llm.ainvoke([
            {"role": "system", "content": RE_RANK_PROMPT},
            {"role": "user", "content": f"Query: {query}\n\nRetrieved passages:\n{combined}"},
        ])
        return response.content
    except Exception as exc:
        logger.exception(f"Answer synthesis failed: {exc}")
        return f"Retrieved {len(chunk_texts)} relevant chunks from the knowledge base but failed to synthesize an answer."


def _not_found_result(query: str) -> dict[str, Any]:
    return {
        "agent": "knowledge_agent",
        "status": "completed",
        "result": {
            "answer": "No relevant information found in your company knowledge base. Try rephrasing your query or uploading relevant documents first.",
            "sources": [],
            "conflicts_detected": False,
            "conflicts": [],
            "total_results": 0,
        },
        "context_updates": {"last_knowledge_query": query},
        "requires_approval": False,
    }
