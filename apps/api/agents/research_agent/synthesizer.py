import logging
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any, Optional

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from core.config import settings
from agents.supervisor.prompts import INJECTION_GUARDRAIL

logger = logging.getLogger("agents.research_agent.synthesizer")

SIMILARITY_THRESHOLD = 0.6  # Flag passages with >60% overlap against source
MAX_PASSAGE_LENGTH = 200  # Check passages of this length for similarity

SYNTHESIS_PROMPT = """You are a market research analyst. Synthesize the provided web search results
into a structured market research report about the given company.

The report must contain these sections:
1. **Executive Summary** — 2-3 sentence overview of the company and its market position
2. **Company Overview** — what they do, founding, size, headquarters
3. **SWOT Analysis** — Strengths, Weaknesses, Opportunities, and Threats in a structured format
4. **Competitors** — key competitors and how they compare
5. **Recent News** — notable recent developments with dates
6. **Opportunities** — market opportunities identified from the data
7. **Risks** — risks or challenges facing the company

Rules:
- CRITICAL: Paraphrase everything. Do NOT reproduce large verbatim passages from sources.
  Use your own words to summarize findings. Rephrase, condense, and add analytical value.
- Each claim MUST be tagged with its source URL AND retrieval timestamp in brackets,
  e.g. [source_url @ 2026-07-25 12:00 UTC]
- If information is unavailable for a section, say "No data found" rather than fabricating
- Base your analysis ONLY on the provided search results — do not add external knowledge
- Be objective and balanced
- Keep each section focused and concise

""" + INJECTION_GUARDRAIL


class ResearchReport(BaseModel):
    """Structured market research report with SWOT analysis."""
    executive_summary: str = Field(description="2-3 sentence overview")
    company_overview: str = Field(description="What they do, founding, size, location")
    swot_analysis: str = Field(
        description="SWOT analysis: Strengths, Weaknesses, Opportunities, Threats"
    )
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
    """Synthesize crawl results into a structured report with SWOT and similarity check."""
    context = _build_context(company, crawl_results)
    source_texts = _extract_source_texts(crawl_results)

    # Build list of LLMs to try (cascading fallback)
    llms_to_try: list[ChatOpenAI] = []
    if llm is not None:
        llms_to_try.append(llm)
    else:
        from core.llm_factory import get_provider_candidates
        for cand in get_provider_candidates(is_classifier=False):
            kwargs = {
                "model": cand["model"],
                "temperature": 0.2,
                "api_key": cand["api_key"],
            }
            if cand.get("base_url"):
                kwargs["base_url"] = cand["base_url"]
            llms_to_try.append(ChatOpenAI(**kwargs))

    last_exc = None
    for candidate_llm in llms_to_try:
        # Attempt 1: structured output (function calling)
        try:
            structured = candidate_llm.with_structured_output(ResearchReport)
            result = await structured.ainvoke([
                {"role": "system", "content": SYNTHESIS_PROMPT},
                {"role": "user", "content": context},
            ])
            result.report_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            logger.info(f"Synthesized research report for '{company}' via structured output")
            _check_similarity(result, source_texts)
            return result
        except Exception as exc:
            logger.warning(f"Structured output synthesis failed: {exc}. Trying plain text fallback...")
            last_exc = exc

        # Attempt 2: plain text invoke + manual JSON parsing
        try:
            import json as _json
            plain_prompt = SYNTHESIS_PROMPT + """

IMPORTANT: Return your response as a valid JSON object with these exact keys:
{
  "executive_summary": "...",
  "company_overview": "...",
  "swot_analysis": "Strengths: ... Weaknesses: ... Opportunities: ... Threats: ...",
  "competitors": "...",
  "recent_news": "...",
  "opportunities": "...",
  "risks": "...",
  "report_date": "YYYY-MM-DD"
}

Return ONLY the JSON object, no markdown fences or extra text."""

            response = await candidate_llm.ainvoke([
                {"role": "system", "content": plain_prompt},
                {"role": "user", "content": context},
            ])
            text = response.content.strip()
            # Try to extract JSON from the response
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()

            data = _json.loads(text)
            result = ResearchReport(
                executive_summary=data.get("executive_summary", "No data found."),
                company_overview=data.get("company_overview", "No data found."),
                swot_analysis=data.get("swot_analysis", "No data found."),
                competitors=data.get("competitors", "No data found."),
                recent_news=data.get("recent_news", "No data found."),
                opportunities=data.get("opportunities", "No data found."),
                risks=data.get("risks", "No data found."),
                report_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            )
            logger.info(f"Synthesized research report for '{company}' via plain text fallback")
            _check_similarity(result, source_texts)
            return result
        except Exception as exc2:
            logger.warning(f"Plain text synthesis also failed: {exc2}. Trying next provider...")
            last_exc = exc2

    logger.exception(f"All synthesis attempts failed for '{company}': {last_exc}")
    return ResearchReport(
        executive_summary=f"Failed to synthesize full report for {company}.",
        company_overview="No data found.",
        swot_analysis="No data found.",
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
    """Build the context string fed to the LLM for synthesis."""
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


def _extract_source_texts(crawl_results: dict[str, list[dict[str, Any]]]) -> list[str]:
    """Extract all source content strings for similarity checking."""
    texts = []
    for category_results in crawl_results.values():
        for r in category_results:
            content = r.get("content", "")
            if content and not content.startswith("["):
                texts.append(content)
    return texts


def _check_similarity(report: ResearchReport, source_texts: list[str]) -> None:
    """Post-generation similarity check (PRD 5.12 copyright constraint).

    Checks each report section against source texts. If any passage has >60%
    similarity with a source, it is logged as a warning. This is a non-blocking
    check — the report is still returned, but the violation is recorded.
    """
    if not source_texts:
        return

    sections = {
        "executive_summary": report.executive_summary,
        "company_overview": report.company_overview,
        "swot_analysis": report.swot_analysis,
        "competitors": report.competitors,
        "recent_news": report.recent_news,
        "opportunities": report.opportunities,
        "risks": report.risks,
    }

    violations_found = 0
    for section_name, section_text in sections.items():
        if not section_text or section_text == "No data found.":
            continue

        # Check sliding windows of the section text against source texts
        for source in source_texts:
            if len(source) < 50:
                continue
            # Check overlapping chunks of the generated text
            for start in range(0, max(1, len(section_text) - MAX_PASSAGE_LENGTH + 1), 50):
                passage = section_text[start:start + MAX_PASSAGE_LENGTH]
                ratio = SequenceMatcher(None, passage.lower(), source[:1000].lower()).ratio()
                if ratio > SIMILARITY_THRESHOLD:
                    violations_found += 1
                    logger.warning(
                        f"Similarity violation in '{section_name}': "
                        f"{ratio:.1%} overlap with source text at offset {start}. "
                        f"Passage: '{passage[:80]}...'"
                    )
                    break  # One violation per source per section is enough

    if violations_found:
        logger.warning(
            f"Post-generation similarity check found {violations_found} potential "
            f"verbatim reproduction(s). Review report for paraphrasing compliance."
        )
    else:
        logger.info("Post-generation similarity check passed — no verbatim reproductions detected.")
