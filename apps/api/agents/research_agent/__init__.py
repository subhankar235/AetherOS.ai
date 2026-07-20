import hashlib
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from qdrant_client.http import models as qdrant_models

from core.config import settings
from integrations.qdrant_client import qdrant_client
from agents.research_agent.planner import plan_research
from agents.research_agent.crawler import crawl_queries
from agents.research_agent.synthesizer import synthesize_report

logger = logging.getLogger("agents.research_agent")

CACHE_TTL_HOURS = 24


async def run_research(
    company: str,
    context: Optional[str] = None,
) -> dict[str, Any]:
    plan = await plan_research(company, context)

    if plan.is_ambiguous:
        return {
            "agent": "research_agent",
            "status": "clarification_needed",
            "result": {
                "clarification": plan.clarification_question,
                "company": company,
            },
            "context_updates": {},
            "requires_approval": False,
        }

    if not plan.queries:
        return {
            "agent": "research_agent",
            "status": "completed",
            "result": {
                "executive_summary": f"Research could not be planned for '{company}'.",
                "company_overview": "No data found.",
                "competitors": "No data found.",
                "recent_news": "No data found.",
                "opportunities": "No data found.",
                "risks": "No data found.",
                "report_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            },
            "context_updates": {"last_research_query": company},
            "requires_approval": False,
        }

    cached = await _check_cache(company, context)
    if cached is not None:
        logger.info(f"Using cached research for '{company}'")
        cached["_from_cache"] = True
        cached["_cache_hit"] = True
        return cached

    crawl_results = await crawl_queries(plan.queries)

    report = await synthesize_report(company, crawl_results)

    result = _build_result(company, report)
    await _write_cache(company, context, result)

    return result


def _build_result(company: str, report) -> dict[str, Any]:
    return {
        "agent": "research_agent",
        "status": "completed",
        "result": {
            "executive_summary": report.executive_summary,
            "company_overview": report.company_overview,
            "competitors": report.competitors,
            "recent_news": report.recent_news,
            "opportunities": report.opportunities,
            "risks": report.risks,
            "report_date": report.report_date,
        },
        "context_updates": {"last_research_query": company},
        "requires_approval": False,
    }


async def _check_cache(
    company: str,
    context: Optional[str],
) -> Optional[dict[str, Any]]:
    cache_key = _cache_key(company, context)
    try:
        client = qdrant_client.get_client()
        result = await client.retrieve(
            collection_name=settings.QDRANT_COLLECTION_RESEARCH_CACHE,
            ids=[cache_key],
        )
        if result:
            point = result[0]
            payload = point.payload or {}
            cached_at_str = payload.get("cached_at", "")
            if cached_at_str:
                try:
                    cached_at = datetime.fromisoformat(cached_at_str)
                    age = datetime.now(timezone.utc) - cached_at
                    if age < timedelta(hours=CACHE_TTL_HOURS):
                        return payload.get("result")
                except ValueError:
                    pass
            logger.info(f"Research cache entry for '{company}' expired or invalid")
        return None
    except Exception as exc:
        logger.warning(f"Research cache read failed: {exc}")
        return None


async def _write_cache(
    company: str,
    context: Optional[str],
    result: dict[str, Any],
) -> None:
    cache_key = _cache_key(company, context)
    try:
        await qdrant_client.upsert(
            collection_name=settings.QDRANT_COLLECTION_RESEARCH_CACHE,
            points=[
                qdrant_models.PointStruct(
                    id=cache_key,
                    vector=[0.0] * 3072,
                    payload={
                        "company": company,
                        "context": context or "",
                        "result": result,
                        "cached_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
            ],
        )
        logger.info(f"Cached research result for '{company}'")
    except Exception as exc:
        logger.warning(f"Failed to cache research result: {exc}")


def _cache_key(company: str, context: Optional[str]) -> str:
    raw = f"{company.lower().strip()}|{context or ''}"
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, raw))


__all__ = [
    "run_research",
]
