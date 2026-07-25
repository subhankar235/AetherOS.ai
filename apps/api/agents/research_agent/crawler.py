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
    """Crawl all category queries in parallel and return enriched results."""
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
    """Search a single category, then fetch/enrich each result page."""
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


# ---------------------------------------------------------------------------
# Web Search — cascading fallback: Tavily -> Brave -> Serper -> simulated
# ---------------------------------------------------------------------------

async def _web_search(
    client: httpx.AsyncClient,
    query: str,
) -> list[dict[str, str]]:
    """Try search providers in order until one succeeds."""
    # 1. Tavily
    results = await _try_tavily(client, query)
    if results:
        return results

    # 2. Brave Search
    results = await _try_brave(client, query)
    if results:
        return results

    # 3. Serper (Google Search wrapper)
    results = await _try_serper(client, query)
    if results:
        return results

    # 4. Simulated fallback for development
    logger.info("All search providers unavailable, using simulated search results")
    return _simulated_search(query)


async def _try_tavily(
    client: httpx.AsyncClient,
    query: str,
) -> Optional[list[dict[str, str]]]:
    """Tavily search API."""
    api_key = getattr(settings, "TAVILY_API_KEY", None) or ""
    if not api_key or api_key.startswith("tvly-xxxx"):
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
        logger.debug(f"Tavily returned {len(raw_results)} results for '{query[:50]}'")
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


async def _try_brave(
    client: httpx.AsyncClient,
    query: str,
) -> Optional[list[dict[str, str]]]:
    """Brave Search API fallback."""
    api_key = getattr(settings, "BRAVE_SEARCH_API_KEY", None) or ""
    if not api_key or api_key.startswith("xxxx"):
        return None

    try:
        resp = await client.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": query, "count": MAX_RESULTS_PER_QUERY},
            headers={"X-Subscription-Token": api_key, "Accept": "application/json"},
            timeout=SEARCH_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        web_results = data.get("web", {}).get("results", [])
        logger.debug(f"Brave returned {len(web_results)} results for '{query[:50]}'")
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("description", ""),
            }
            for r in web_results
        ]
    except Exception as exc:
        logger.debug(f"Brave search failed for '{query[:60]}...': {exc}")
        return None


async def _try_serper(
    client: httpx.AsyncClient,
    query: str,
) -> Optional[list[dict[str, str]]]:
    """Serper.dev Google Search API fallback."""
    api_key = getattr(settings, "SERPER_API_KEY", None) or ""
    if not api_key or api_key.startswith("xxxx"):
        return None

    try:
        resp = await client.post(
            "https://google.serper.dev/search",
            json={"q": query, "num": MAX_RESULTS_PER_QUERY},
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            timeout=SEARCH_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        organic = data.get("organic", [])
        logger.debug(f"Serper returned {len(organic)} results for '{query[:50]}'")
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("link", ""),
                "content": r.get("snippet", ""),
            }
            for r in organic
        ]
    except Exception as exc:
        logger.debug(f"Serper search failed for '{query[:60]}...': {exc}")
        return None


def _simulated_search(query: str) -> list[dict[str, str]]:
    """Fallback simulated results when no search API is configured."""
    import hashlib
    query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
    return [
        {
            "title": f"Search result about {query[:50]}",
            "url": f"https://example.com/results/{query_hash}",
            "content": f"This is a simulated search result for '{query}'. "
                       f"In production, configure TAVILY_API_KEY, BRAVE_SEARCH_API_KEY, "
                       f"or SERPER_API_KEY for real web search results.",
        }
    ]


# ---------------------------------------------------------------------------
# Page Content Fetch — cascading: httpx -> Firecrawl -> Playwright -> skip
# ---------------------------------------------------------------------------

async def _fetch_page_content(
    client: httpx.AsyncClient,
    url: str,
    title: str,
) -> Optional[dict[str, Any]]:
    """Fetch page content with cascading fallbacks for JS-heavy / paywalled pages."""
    now = datetime.now(timezone.utc)
    base = {
        "title": title,
        "url": url,
        "fetched_at": now.isoformat(),
        "timestamp": now.strftime("%Y-%m-%d %H:%M UTC"),
    }

    # 1. Direct HTTP fetch (fast, works for most pages)
    content = await _try_direct_fetch(client, url)
    if content and len(content.strip()) > 100:
        return {**base, "content": content[:MAX_CONTENT_LENGTH]}

    # 2. Firecrawl (targeted crawl, handles JS rendering)
    content = await _try_firecrawl(client, url)
    if content and len(content.strip()) > 100:
        return {**base, "content": content[:MAX_CONTENT_LENGTH], "source": "firecrawl"}

    # 3. Playwright (local headless browser, JS-heavy fallback)
    content = await _try_playwright(url)
    if content and len(content.strip()) > 100:
        return {**base, "content": content[:MAX_CONTENT_LENGTH], "source": "playwright"}

    # 4. Graceful skip — note that content was unavailable
    if content:
        return {**base, "content": content[:MAX_CONTENT_LENGTH]}

    return {
        **base,
        "content": "[Content unavailable: all fetch methods failed or page is paywalled/unreachable]",
        "error": "all_fetch_methods_failed",
    }


async def _try_direct_fetch(
    client: httpx.AsyncClient,
    url: str,
) -> Optional[str]:
    """Simple HTTP GET fetch."""
    try:
        resp = await client.get(url, timeout=FETCH_TIMEOUT, follow_redirects=True)
        resp.raise_for_status()
        return resp.text
    except Exception as exc:
        logger.debug(f"Direct fetch failed for '{url}': {type(exc).__name__}")
        return None


async def _try_firecrawl(
    client: httpx.AsyncClient,
    url: str,
) -> Optional[str]:
    """Firecrawl API for targeted crawl with JS rendering and clean markdown output."""
    api_key = getattr(settings, "FIRECRAWL_API_KEY", None) or ""
    if not api_key or api_key.startswith("fc-xxxx"):
        return None

    try:
        resp = await client.post(
            "https://api.firecrawl.dev/v1/scrape",
            json={
                "url": url,
                "formats": ["markdown"],
                "onlyMainContent": True,
            },
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=FETCH_TIMEOUT + 10,  # Firecrawl can be slower due to rendering
        )
        resp.raise_for_status()
        data = resp.json()
        markdown = data.get("data", {}).get("markdown", "")
        if markdown:
            logger.debug(f"Firecrawl extracted {len(markdown)} chars from '{url}'")
            return markdown
        return None
    except Exception as exc:
        logger.debug(f"Firecrawl failed for '{url}': {type(exc).__name__}: {exc}")
        return None


async def _try_playwright(url: str) -> Optional[str]:
    """Playwright headless browser fallback for JS-heavy pages."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.debug("Playwright not installed, skipping JS-render fallback")
        return None

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            # Wait a moment for JS to render
            await page.wait_for_timeout(2000)
            text = await page.inner_text("body")
            await browser.close()
            if text:
                logger.debug(f"Playwright extracted {len(text)} chars from '{url}'")
                return text
            return None
    except Exception as exc:
        logger.debug(f"Playwright failed for '{url}': {type(exc).__name__}: {exc}")
        return None
