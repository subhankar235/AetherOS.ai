import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from core.config import settings

logger = logging.getLogger("agents.research_agent.crawler")

SEARCH_TIMEOUT = 15
FETCH_TIMEOUT = 10
MAX_RESULTS_PER_QUERY = 5
MAX_CONTENT_LENGTH = 3000


async def crawl_queries(queries: dict[str, str]) -> dict[str, list[dict[str, Any]]]:
    results: dict[str, list[dict[str, Any]]] = {}

    async with httpx.AsyncClient(timeout=SEARCH_TIMEOUT) as client:
        tasks = []
        for category, query in queries.items():
            tasks.append(_search_category(client, category, query))
        outcomes = await asyncio.gather(*tasks, return_exceptions=True)

    for outcome in outcomes:
        if isinstance(outcome, Exception):
            logger.warning(f"Research crawl task failed: {outcome}")
            continue
        if isinstance(outcome, tuple):
            category, category_results = outcome
            results[category] = category_results

    return results


async def _search_category(
    client: httpx.AsyncClient,
    category: str,
    query: str,
) -> tuple[str, list[dict[str, Any]]]:
    try:
        search_results = await _web_search(client, query)
    except Exception as exc:
        logger.warning(f"Search failed for query '{query[:60]}...': {exc}")
        return category, []

    fetch_tasks = []
    for sr in search_results[:MAX_RESULTS_PER_QUERY]:
        url = sr.get("url", "")
        if url:
            fetch_tasks.append(_fetch_page_content(client, url, sr.get("title", "")))

    content_results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

    enriched: list[dict[str, Any]] = []
    for item in content_results:
        if isinstance(item, Exception):
            continue
        if item:
            enriched.append(item)

    logger.info(
        f"Crawled '{category}': {len(enriched)} results from {len(search_results)} search hits"
    )
    return category, enriched


async def _web_search(
    client: httpx.AsyncClient,
    query: str,
) -> list[dict[str, str]]:
    results = await _try_tavily(client, query)
    if results:
        return results
    logger.info("Tavily unavailable, using simulated search results")
    return _simulated_search(query)


async def _try_tavily(
    client: httpx.AsyncClient,
    query: str,
) -> Optional[list[dict[str, str]]]:
    api_key = getattr(settings, "TAVILY_API_KEY", None) or ""
    if not api_key or api_key == "tvly-xxxxxxxxxxxxx":
        return None

    try:
        resp = await client.post(
            "https://api.tavily.com/search",
            json={"api_key": api_key, "query": query, "max_results": MAX_RESULTS_PER_QUERY},
            timeout=SEARCH_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        raw_results = data.get("results", [])
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", ""),
            }
            for r in raw_results
        ]
    except Exception as exc:
        logger.debug(f"Tavily search failed for '{query[:60]}...': {exc}")
        return None


def _simulated_search(query: str) -> list[dict[str, str]]:
    import hashlib
    query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
    return [
        {
            "title": f"Search result about {query[:50]}",
            "url": f"https://example.com/results/{query_hash}",
            "content": f"This is a simulated search result for '{query}'. "
                       f"In production, configure TAVILY_API_KEY for real web search results.",
        }
    ]


async def _fetch_page_content(
    client: httpx.AsyncClient,
    url: str,
    title: str,
) -> Optional[dict[str, Any]]:
    try:
        resp = await client.get(url, timeout=FETCH_TIMEOUT, follow_redirects=True)
        resp.raise_for_status()
        text = resp.text[:MAX_CONTENT_LENGTH]
        now = datetime.now(timezone.utc)
        return {
            "title": title,
            "url": url,
            "content": text,
            "fetched_at": now.isoformat(),
            "timestamp": now.strftime("%Y-%m-%d %H:%M UTC"),
        }
    except Exception as exc:
        logger.debug(f"Failed to fetch '{url}': {type(exc).__name__}")
        return {
            "title": title,
            "url": url,
            "content": f"[Content unavailable: {type(exc).__name__}]",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "error": str(exc),
        }
