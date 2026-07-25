"""
Phase 15 — Market Research Agent: FULL WORKFLOW DEMO
Shows exact input -> output at every pipeline stage for a real company.
"""
import asyncio
import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("CLERK_SECRET_KEY", "test")
os.environ.setdefault("CLERK_PUBLISHABLE_KEY", "test")
os.environ.setdefault("CLERK_WEBHOOK_SIGNING_SECRET", "test")


def sep(title):
    print(f"\n{'='*70}")
    print(f"  STAGE: {title}")
    print(f"{'='*70}\n")


def pretty(obj, indent=2):
    if hasattr(obj, "model_dump"):
        obj = obj.model_dump()
    print(json.dumps(obj, indent=indent, default=str, ensure_ascii=False))


async def run_full_workflow():
    from core.config import settings

    # ==============================================================
    # USER INPUT
    # ==============================================================
    COMPANY = "Stripe"
    CONTEXT = None  # No extra context provided

    sep("0 - USER INPUT")
    print(f"  User says: \"Research Stripe\"")
    print(f"  Parsed ->  company = \"{COMPANY}\"")
    print(f"             context = {CONTEXT}")

    total_start = time.time()

    # ==============================================================
    # STAGE 1: PLANNER — Disambiguation Check
    # ==============================================================
    sep("1 - PLANNER: Disambiguation Check")
    print("  Input:  company=\"Stripe\", context=None")
    print("  Action: LLM checks if 'Stripe' is ambiguous...\n")

    from agents.research_agent.planner import _check_ambiguity, plan_research, ResearchPlan
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
        api_key=settings.OPENAI_API_KEY,
    )
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith("sk-or-v1"):
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=settings.OPENAI_API_KEY,
            base_url="https://openrouter.ai/api/v1",
        )

    disambig = await _check_ambiguity(COMPANY, CONTEXT, llm)
    print(f"  Output:")
    print(f"    is_ambiguous: {disambig.is_ambiguous}")
    print(f"    clarification_question: \"{disambig.clarification_question}\"")
    if disambig.is_ambiguous:
        print(f"\n  >> WOULD STOP HERE and ask user: \"{disambig.clarification_question}\"")
        print(f"  >> But for demo, continuing anyway...")
    else:
        print(f"\n  >> 'Stripe' is NOT ambiguous. Proceeding to query generation.")

    # ==============================================================
    # STAGE 2: PLANNER — Query Decomposition
    # ==============================================================
    sep("2 - PLANNER: Query Decomposition into 5 Sub-Queries")
    print("  Input:  company=\"Stripe\", context=None")
    print("  Action: LLM generates 5 targeted search queries...\n")

    t0 = time.time()
    plan = await plan_research(COMPANY, CONTEXT, llm)
    planner_time = time.time() - t0

    print(f"  Output (in {planner_time:.1f}s):")
    for category, query in plan.queries.items():
        print(f"    [{category:12s}] -> \"{query}\"")
    print(f"\n  Total queries generated: {len(plan.queries)}")

    # ==============================================================
    # STAGE 3: CRAWLER — Parallel Web Search (Tavily)
    # ==============================================================
    sep("3 - CRAWLER: Parallel Web Search via Tavily")
    print(f"  Input:  {len(plan.queries)} queries (one per category)")
    print(f"  Action: Searching all 5 categories in PARALLEL via Tavily API...")
    print(f"  Fallback chain: Tavily -> Brave -> Serper -> Simulated\n")

    from agents.research_agent.crawler import crawl_queries

    t0 = time.time()
    crawl_results = await crawl_queries(plan.queries)
    crawl_time = time.time() - t0

    total_sources = 0
    print(f"  Output (in {crawl_time:.1f}s):")
    for category, items in crawl_results.items():
        total_sources += len(items)
        print(f"\n  [{category.upper()}] - {len(items)} sources found:")
        for i, item in enumerate(items[:3], 1):
            title = item.get("title", "?")[:55]
            url = item.get("url", "?")[:65]
            ts = item.get("timestamp", "no timestamp")
            content_len = len(item.get("content", ""))
            source = item.get("source", "direct")
            print(f"    {i}. \"{title}\"")
            print(f"       URL: {url}")
            print(f"       Fetched: {ts} | Content: {content_len} chars | Via: {source}")
        if len(items) > 3:
            print(f"    ... and {len(items)-3} more")

    print(f"\n  Total sources fetched: {total_sources}")

    # ==============================================================
    # STAGE 4: SYNTHESIZER — GPT Report Generation
    # ==============================================================
    sep("4 - SYNTHESIZER: GPT Report Generation with SWOT")
    print(f"  Input:  {total_sources} source documents across {len(crawl_results)} categories")
    print(f"  Action: LLM synthesizes structured report with SWOT analysis...")
    print(f"  Rules:  Paraphrase only, per-claim [url @ timestamp] tagging\n")

    from agents.research_agent.synthesizer import synthesize_report

    t0 = time.time()
    report = await synthesize_report(COMPANY, crawl_results, llm)
    synth_time = time.time() - t0

    print(f"  Output (in {synth_time:.1f}s):\n")
    print(f"  --- EXECUTIVE SUMMARY ---")
    print(f"  {report.executive_summary}\n")
    print(f"  --- COMPANY OVERVIEW ---")
    print(f"  {report.company_overview}\n")
    print(f"  --- SWOT ANALYSIS ---")
    print(f"  {report.swot_analysis}\n")
    print(f"  --- COMPETITORS ---")
    print(f"  {report.competitors}\n")
    print(f"  --- RECENT NEWS ---")
    print(f"  {report.recent_news}\n")
    print(f"  --- OPPORTUNITIES ---")
    print(f"  {report.opportunities}\n")
    print(f"  --- RISKS ---")
    print(f"  {report.risks}\n")
    print(f"  --- REPORT DATE ---")
    print(f"  {report.report_date}")

    # ==============================================================
    # STAGE 5: SIMILARITY CHECK (PRD 5.12)
    # ==============================================================
    sep("5 - SIMILARITY CHECK: Anti-Verbatim (PRD 5.12)")
    print(f"  Input:  Generated report + {total_sources} source texts")
    print(f"  Action: Sliding-window comparison (60% threshold)...")

    from agents.research_agent.synthesizer import _check_similarity, _extract_source_texts

    source_texts = _extract_source_texts(crawl_results)
    print(f"  Source texts to check against: {len(source_texts)}")
    _check_similarity(report, source_texts)
    print(f"  (See log output above for any violations)")

    # ==============================================================
    # STAGE 6: CACHE WRITE
    # ==============================================================
    sep("6 - CACHE: Write Result to Qdrant")
    from agents.research_agent import _cache_key
    cache_key = _cache_key(COMPANY, CONTEXT)
    print(f"  Input:  company=\"{COMPANY}\", context={CONTEXT}")
    print(f"  Cache key: {cache_key}")
    print(f"  Collection: research_cache")
    print(f"  TTL: 24 hours")
    print(f"  Action: Would upsert to Qdrant (skipped in demo - needs running Qdrant)")

    # ==============================================================
    # STAGE 7: FINAL API RESPONSE
    # ==============================================================
    sep("7 - FINAL API RESPONSE (what the frontend receives)")
    from agents.research_agent import _build_result
    final_result = _build_result(COMPANY, report)

    total_time = time.time() - total_start

    pretty(final_result)

    # ==============================================================
    # TIMING SUMMARY
    # ==============================================================
    sep("TIMING SUMMARY")
    print(f"  Planner (disambiguation + query gen): {planner_time:.1f}s")
    print(f"  Crawler (parallel search + fetch):     {crawl_time:.1f}s")
    print(f"  Synthesizer (GPT report):              {synth_time:.1f}s")
    print(f"  -----------------------------------------------")
    print(f"  TOTAL END-TO-END:                      {total_time:.1f}s")
    print(f"\n  Sources crawled: {total_sources}")
    print(f"  Report sections: 7 (incl. SWOT)")
    print(f"  Cache: write-through on Qdrant (24h TTL)")

    # ==============================================================
    # DISAMBIGUATION DEMO
    # ==============================================================
    sep("BONUS - DISAMBIGUATION DEMO: Ambiguous Input")
    print("  Input:  company=\"Apple\", context=None")
    print("  Action: LLM checks if 'Apple' is ambiguous...\n")

    disambig2 = await _check_ambiguity("Apple", None, llm)
    print(f"  Output:")
    print(f"    is_ambiguous: {disambig2.is_ambiguous}")
    print(f"    clarification_question: \"{disambig2.clarification_question}\"")
    if disambig2.is_ambiguous:
        print(f"\n  >> Pipeline STOPS here. User is asked:")
        print(f"  >> \"{disambig2.clarification_question}\"")
        print(f"  >> Once user responds (e.g. 'Apple Inc, technology'),")
        print(f"  >> the pipeline restarts with context='technology'")
    else:
        print(f"  >> LLM determined 'Apple' is unambiguous (defaulted to Apple Inc.)")

    print(f"\n{'='*70}")
    print(f"  WORKFLOW DEMO COMPLETE")
    print(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(run_full_workflow())
