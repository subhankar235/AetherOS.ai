import logging
from datetime import datetime, timezone
from typing import Any, Optional

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from core.config import settings
from agents.supervisor.prompts import INJECTION_GUARDRAIL

logger = logging.getLogger("agents.research_agent.synthesizer")

SYNTHESIS_PROMPT = """You are a market research analyst. Synthesize the provided web search results
into a structured market research report about the given company.

The report must contain these sections:
1. **Executive Summary** — 2-3 sentence overview of the company and its market position
2. **Company Overview** — what they do, founding, size, headquarters
3. **Competitors** — key competitors and how they compare
4. **Recent News** — notable recent developments with dates
5. **Opportunities** — market opportunities identified from the data
6. **Risks** — risks or challenges facing the company

Rules:
- CRITICAL: Paraphrase everything. Do NOT reproduce large verbatim passages from sources.
  Use your own words to summarize findings.
- Each claim MUST be tagged with its source URL in brackets, e.g. [source_url]
- If information is unavailable for a section, say "No data found" rather than fabricating
- Base your analysis ONLY on the provided search results — do not add external knowledge
- Be objective and balanced

""" + INJECTION_GUARDRAIL


class ResearchReport(BaseModel):
    executive_summary: str = Field(description="2-3 sentence overview")
    company_overview: str = Field(description="What they do, founding, size, location")
    competitors: str = Field(description="Key competitors and comparison")
    recent_news: str = Field(description="Notable recent developments with dates")
    opportunities: str = Field(description="Market opportunities")
    risks: str = Field(description="Risks or challenges")
    report_date: str = Field(description="ISO date of report generation")


async def synthesize_report(
    company: str,
    crawl_results: dict[str, list[dict[str, Any]]],
    llm: Optional[ChatOpenAI] = None,
) -> ResearchReport:
    if llm is None:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.2,
            api_key=settings.OPENAI_API_KEY,
        )

    context = _build_context(company, crawl_results)

    structured = llm.with_structured_output(ResearchReport)
    try:
        result = await structured.ainvoke([
            {"role": "system", "content": SYNTHESIS_PROMPT},
            {"role": "user", "content": context},
        ])
        result.report_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        logger.info(f"Synthesized research report for '{company}'")
        return result
    except Exception as exc:
        logger.exception(f"Report synthesis failed: {exc}")
        return ResearchReport(
            executive_summary=f"Failed to synthesize full report for {company}.",
            company_overview="No data found.",
            competitors="No data found.",
            recent_news="No data found.",
            opportunities="No data found.",
            risks="No data found.",
            report_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        )


def _build_context(
    company: str,
    crawl_results: dict[str, list[dict[str, Any]]],
) -> str:
    parts = [f"# Market Research Report for: {company}\n"]

    for category in ["overview", "competitors", "news", "pricing", "reviews"]:
        results = crawl_results.get(category, [])
        if not results:
            continue

        parts.append(f"\n## {category.upper()} Search Results\n")
        for i, r in enumerate(results, 1):
            title = r.get("title", "Untitled")
            url = r.get("url", "")
            content = r.get("content", "")[:2000]
            ts = r.get("timestamp", "")
            parts.append(f"### Source {i}: {title}")
            if ts:
                parts.append(f"Fetched: {ts}")
            parts.append(f"URL: {url}")
            parts.append(f"Content:\n{content}\n")

    return "\n".join(parts)
