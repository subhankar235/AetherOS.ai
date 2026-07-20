import logging
from typing import Any, Optional

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from core.config import settings

logger = logging.getLogger("agents.research_agent.planner")

SUB_QUERY_CATEGORIES = ["overview", "competitors", "news", "pricing", "reviews"]

PLANNER_PROMPT = """You are a market research planner. Your job is to decompose a research request
about a company into specific, targeted search queries that will produce a comprehensive market report.

For each category below, produce one specific search query:
- **overview**: Company background, what they do, founding, size
- **competitors**: Main competitors, competitive landscape
- **news**: Recent news, announcements, developments (last 6 months)
- **pricing**: Pricing model, plans, or cost structure (if applicable)
- **reviews**: Customer reviews, ratings, user sentiment

Rules:
- Make queries specific and search-engine-friendly (use quotes, include the company name)
- Do not fabricate — these queries are for actual web search
- If the user provided extra context (industry, domain, etc.), incorporate it to disambiguate
"""

DISAMBIGUATION_PROMPT = """Given the company name and any available context, determine if the name is ambiguous.
A company name is ambiguous if it could refer to multiple distinct entities (e.g., "Apple" could be Apple Inc.
or the fruit; "Delta" could be Delta Air Lines or Delta Faucet).

If ambiguous, return `is_ambiguous: true` and a clarification question.
If not ambiguous, return `is_ambiguous: false` and an empty clarification.

Available context from the user: {context}
"""


class ResearchPlan(BaseModel):
    queries: dict[str, str] = Field(
        description="One search query per category: overview, competitors, news, pricing, reviews"
    )
    is_ambiguous: bool = Field(default=False)
    clarification_question: str = Field(default="", description="Question to ask user if ambiguous")


async def plan_research(
    company: str,
    context: Optional[str] = None,
    llm: Optional[ChatOpenAI] = None,
) -> ResearchPlan:
    if llm is None:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=settings.OPENAI_API_KEY,
        )

    disambiguation = await _check_ambiguity(company, context, llm)
    if disambiguation.is_ambiguous:
        return disambiguation

    structured = llm.with_structured_output(ResearchPlan)
    try:
        result = await structured.ainvoke([
            {"role": "system", "content": PLANNER_PROMPT},
            {
                "role": "user",
                "content": f"Company: {company}"
                           + (f"\nContext: {context}" if context else ""),
            },
        ])
        logger.info(f"Planned {len(result.queries)} research queries for '{company}'")
        for cat, q in result.queries.items():
            logger.debug(f"  [{cat}] {q}")
        return result
    except Exception as exc:
        logger.exception(f"Research planning failed: {exc}")
        return ResearchPlan(
            queries={
                "overview": f"{company} company overview",
                "competitors": f"{company} competitors",
                "news": f"{company} latest news 2026",
                "pricing": f"{company} pricing",
                "reviews": f"{company} reviews",
            },
        )


async def _check_ambiguity(
    company: str,
    context: Optional[str],
    llm: ChatOpenAI,
) -> ResearchPlan:
    class AmbiguityCheck(BaseModel):
        is_ambiguous: bool = False
        clarification_question: str = ""

    structured = llm.with_structured_output(AmbiguityCheck)
    try:
        result = await structured.ainvoke([
            {
                "role": "system",
                "content": DISAMBIGUATION_PROMPT.format(context=context or "No additional context provided."),
            },
            {"role": "user", "content": f"Company name: {company}"},
        ])
        if result.is_ambiguous:
            logger.info(f"Ambiguous company name '{company}': {result.clarification_question}")
        return ResearchPlan(
            queries={},
            is_ambiguous=result.is_ambiguous,
            clarification_question=result.clarification_question,
        )
    except Exception as exc:
        logger.warning(f"Ambiguity check failed, assuming unambiguous: {exc}")
        return ResearchPlan(queries={})
