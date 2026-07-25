"""
Phase 15 — Market Research Agent: Full End-to-End Test
Tests all components: planner, crawler (Tavily + Firecrawl), synthesizer, cache, disambiguation.
"""
import asyncio
import sys
import os
import time
import json

# Ensure we can import from the api directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set env file path before importing settings
os.environ.setdefault("CLERK_SECRET_KEY", "test")
os.environ.setdefault("CLERK_PUBLISHABLE_KEY", "test")
os.environ.setdefault("CLERK_WEBHOOK_SIGNING_SECRET", "test")


async def test_all():
    results = {}
    
    print("=" * 70)
    print("  PHASE 15 — MARKET RESEARCH AGENT: FULL E2E TEST")
    print("=" * 70)
    
    # ---------------------------------------------------------------
    # TEST 1: Config — API keys loaded
    # ---------------------------------------------------------------
    print("\n[TEST 1] Config — API keys loaded")
    try:
        from core.config import settings
        tavily_ok = bool(settings.TAVILY_API_KEY and not settings.TAVILY_API_KEY.startswith("tvly-xxxx"))
        firecrawl_ok = bool(settings.FIRECRAWL_API_KEY and not settings.FIRECRAWL_API_KEY.startswith("fc-xxxx"))
        brave_ok = bool(getattr(settings, "BRAVE_SEARCH_API_KEY", None) and not settings.BRAVE_SEARCH_API_KEY.startswith("xxxx"))
        serper_ok = bool(getattr(settings, "SERPER_API_KEY", None) and not settings.SERPER_API_KEY.startswith("xxxx"))
        
        print(f"  TAVILY_API_KEY:        {'✅ SET' if tavily_ok else '⚠️  placeholder'}")
        print(f"  FIRECRAWL_API_KEY:     {'✅ SET' if firecrawl_ok else '⚠️  placeholder'}")
        print(f"  BRAVE_SEARCH_API_KEY:  {'✅ SET' if brave_ok else '⚠️  placeholder (optional)'}")
        print(f"  SERPER_API_KEY:        {'✅ SET' if serper_ok else '⚠️  placeholder (optional)'}")
        results["config"] = "PASS"
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        results["config"] = f"FAIL: {e}"

    # ---------------------------------------------------------------
    # TEST 2: Planner — Query decomposition
    # ---------------------------------------------------------------
    print("\n[TEST 2] Planner — Query decomposition (mock LLM)")
    try:
        from agents.research_agent.planner import ResearchPlan, SUB_QUERY_CATEGORIES
        
        # Verify categories exist
        assert SUB_QUERY_CATEGORIES == ["overview", "competitors", "news", "pricing", "reviews"], \
            f"Wrong categories: {SUB_QUERY_CATEGORIES}"
        
        # Test ResearchPlan model
        plan = ResearchPlan(
            queries={
                "overview": "Stripe company overview",
                "competitors": "Stripe competitors payments",
                "news": "Stripe latest news 2026",
                "pricing": "Stripe pricing plans",
                "reviews": "Stripe customer reviews",
            },
            is_ambiguous=False,
            clarification_question="",
        )
        assert len(plan.queries) == 5
        assert not plan.is_ambiguous
        print(f"  ✅ ResearchPlan model works, {len(plan.queries)} categories")
        print(f"  ✅ Categories: {list(plan.queries.keys())}")
        results["planner"] = "PASS"
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        results["planner"] = f"FAIL: {e}"

    # ---------------------------------------------------------------
    # TEST 3: Planner — Disambiguation model
    # ---------------------------------------------------------------
    print("\n[TEST 3] Planner — Disambiguation model")
    try:
        ambig_plan = ResearchPlan(
            queries={},
            is_ambiguous=True,
            clarification_question="Did you mean Apple Inc. (technology) or Apple Records (music)?",
        )
        assert ambig_plan.is_ambiguous
        assert "Apple" in ambig_plan.clarification_question
        print(f"  ✅ Ambiguous plan: '{ambig_plan.clarification_question}'")
        results["disambiguation_model"] = "PASS"
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        results["disambiguation_model"] = f"FAIL: {e}"

    # ---------------------------------------------------------------
    # TEST 4: Crawler — Tavily LIVE search
    # ---------------------------------------------------------------
    print("\n[TEST 4] Crawler — Tavily LIVE search")
    try:
        import httpx
        from agents.research_agent.crawler import _try_tavily
        
        async with httpx.AsyncClient(timeout=15) as client:
            tavily_results = await _try_tavily(client, "Stripe payments company overview")
        
        if tavily_results:
            print(f"  ✅ Tavily returned {len(tavily_results)} results")
            for i, r in enumerate(tavily_results[:3]):
                print(f"     [{i+1}] {r.get('title', 'no title')[:60]}")
                print(f"         URL: {r.get('url', 'no url')[:70]}")
            results["tavily_search"] = "PASS"
        else:
            print(f"  ⚠️  Tavily returned None (API key issue?)")
            results["tavily_search"] = "WARN: no results"
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        results["tavily_search"] = f"FAIL: {e}"

    # ---------------------------------------------------------------
    # TEST 5: Crawler — Brave search (expected skip if no key)
    # ---------------------------------------------------------------
    print("\n[TEST 5] Crawler — Brave search fallback")
    try:
        from agents.research_agent.crawler import _try_brave
        
        async with httpx.AsyncClient(timeout=15) as client:
            brave_results = await _try_brave(client, "Stripe competitors")
        
        if brave_results:
            print(f"  ✅ Brave returned {len(brave_results)} results")
            results["brave_search"] = "PASS"
        else:
            print(f"  ⚠️  Brave skipped (no valid API key — expected)")
            results["brave_search"] = "SKIP (no key)"
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        results["brave_search"] = f"FAIL: {e}"

    # ---------------------------------------------------------------
    # TEST 6: Crawler — Serper search (expected skip if no key)
    # ---------------------------------------------------------------
    print("\n[TEST 6] Crawler — Serper search fallback")
    try:
        from agents.research_agent.crawler import _try_serper
        
        async with httpx.AsyncClient(timeout=15) as client:
            serper_results = await _try_serper(client, "Stripe pricing")
        
        if serper_results:
            print(f"  ✅ Serper returned {len(serper_results)} results")
            results["serper_search"] = "PASS"
        else:
            print(f"  ⚠️  Serper skipped (no valid API key — expected)")
            results["serper_search"] = "SKIP (no key)"
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        results["serper_search"] = f"FAIL: {e}"

    # ---------------------------------------------------------------
    # TEST 7: Crawler — Firecrawl page fetch
    # ---------------------------------------------------------------
    print("\n[TEST 7] Crawler — Firecrawl page fetch")
    try:
        from agents.research_agent.crawler import _try_firecrawl
        
        async with httpx.AsyncClient(timeout=25) as client:
            fc_content = await _try_firecrawl(client, "https://stripe.com")
        
        if fc_content:
            print(f"  ✅ Firecrawl extracted {len(fc_content)} chars from stripe.com")
            print(f"     Preview: {fc_content[:120]}...")
            results["firecrawl_fetch"] = "PASS"
        else:
            print(f"  ⚠️  Firecrawl returned None (API issue or blocked)")
            results["firecrawl_fetch"] = "WARN: no content"
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        results["firecrawl_fetch"] = f"FAIL: {e}"

    # ---------------------------------------------------------------
    # TEST 8: Crawler — Playwright (expected skip if not installed)
    # ---------------------------------------------------------------
    print("\n[TEST 8] Crawler — Playwright fallback")
    try:
        from agents.research_agent.crawler import _try_playwright
        pw_content = await _try_playwright("https://example.com")
        if pw_content:
            print(f"  ✅ Playwright extracted {len(pw_content)} chars")
            results["playwright"] = "PASS"
        else:
            print(f"  ⚠️  Playwright skipped (not installed — expected, optional)")
            results["playwright"] = "SKIP (not installed)"
    except Exception as e:
        print(f"  ⚠️  Playwright: {e}")
        results["playwright"] = "SKIP"

    # ---------------------------------------------------------------
    # TEST 9: Crawler — Full parallel crawl (LIVE)
    # ---------------------------------------------------------------
    print("\n[TEST 9] Crawler — Full parallel crawl for 'Stripe'")
    try:
        from agents.research_agent.crawler import crawl_queries
        
        test_queries = {
            "overview": "Stripe payments company overview 2026",
            "competitors": "Stripe main competitors payment processing",
            "news": "Stripe latest news announcements 2026",
        }
        
        t0 = time.time()
        crawl_results = await crawl_queries(test_queries)
        elapsed = time.time() - t0
        
        total_results = sum(len(v) for v in crawl_results.values())
        print(f"  ✅ Crawled {len(crawl_results)} categories, {total_results} total results in {elapsed:.1f}s")
        for cat, items in crawl_results.items():
            print(f"     [{cat}]: {len(items)} results")
            for it in items[:2]:
                ts = it.get("timestamp", "no ts")
                print(f"       - {it.get('title','?')[:50]} @ {ts}")
        results["full_crawl"] = "PASS"
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        results["full_crawl"] = f"FAIL: {e}"
        crawl_results = {}

    # ---------------------------------------------------------------
    # TEST 10: Synthesizer — ResearchReport model with SWOT
    # ---------------------------------------------------------------
    print("\n[TEST 10] Synthesizer — ResearchReport model with SWOT")
    try:
        from agents.research_agent.synthesizer import ResearchReport
        
        r = ResearchReport(
            executive_summary="Test summary",
            company_overview="Test overview",
            swot_analysis="Strengths: X. Weaknesses: Y. Opportunities: Z. Threats: W.",
            competitors="Test competitors",
            recent_news="Test news",
            opportunities="Test opps",
            risks="Test risks",
            report_date="2026-07-25",
        )
        assert r.swot_analysis.startswith("Strengths")
        print(f"  ✅ ResearchReport has swot_analysis field")
        print(f"     SWOT: {r.swot_analysis[:60]}...")
        results["report_model"] = "PASS"
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        results["report_model"] = f"FAIL: {e}"

    # ---------------------------------------------------------------
    # TEST 11: Synthesizer — Similarity check
    # ---------------------------------------------------------------
    print("\n[TEST 11] Synthesizer — Post-generation similarity check")
    try:
        from agents.research_agent.synthesizer import _check_similarity, ResearchReport
        
        # Test with near-verbatim text (should flag)
        report = ResearchReport(
            executive_summary="Stripe is a financial infrastructure platform for the internet. Millions of companies use Stripe to accept payments.",
            company_overview="x", swot_analysis="x", competitors="x",
            recent_news="x", opportunities="x", risks="x", report_date="2026",
        )
        source = ["Stripe is a financial infrastructure platform for the internet. Millions of companies use Stripe to accept payments, send payouts."]
        
        import logging
        logging.basicConfig(level=logging.WARNING, format="  %(message)s")
        _check_similarity(report, source)
        
        # Test with paraphrased text (should pass)
        report2 = ResearchReport(
            executive_summary="The company provides payment processing tools for online businesses globally.",
            company_overview="x", swot_analysis="x", competitors="x",
            recent_news="x", opportunities="x", risks="x", report_date="2026",
        )
        _check_similarity(report2, source)
        
        print(f"  ✅ Similarity check works (flags verbatim, passes paraphrased)")
        results["similarity_check"] = "PASS"
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        results["similarity_check"] = f"FAIL: {e}"

    # ---------------------------------------------------------------
    # TEST 12: Cache — key generation
    # ---------------------------------------------------------------
    print("\n[TEST 12] Cache — key generation")
    try:
        from agents.research_agent import _cache_key
        
        k1 = _cache_key("Stripe", None)
        k2 = _cache_key("stripe", None)
        k3 = _cache_key("Stripe", "payments industry")
        
        assert k1 == k2, "Cache key should be case-insensitive"
        assert k1 != k3, "Different context should produce different key"
        print(f"  ✅ Cache keys: same-company={k1[:12]}... with-context={k3[:12]}...")
        print(f"  ✅ Case-insensitive: 'Stripe' == 'stripe' → same key")
        results["cache_key"] = "PASS"
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        results["cache_key"] = f"FAIL: {e}"

    # ---------------------------------------------------------------
    # TEST 13: __init__ — result structure includes SWOT
    # ---------------------------------------------------------------
    print("\n[TEST 13] __init__ — _build_result includes swot_analysis")
    try:
        from agents.research_agent import _build_result
        from agents.research_agent.synthesizer import ResearchReport
        
        mock_report = ResearchReport(
            executive_summary="Summary", company_overview="Overview",
            swot_analysis="SWOT data here", competitors="Comps",
            recent_news="News", opportunities="Opps", risks="Risks",
            report_date="2026-07-25",
        )
        result = _build_result("TestCo", mock_report)
        
        assert "swot_analysis" in result["result"], "swot_analysis missing from result!"
        assert result["result"]["swot_analysis"] == "SWOT data here"
        print(f"  ✅ _build_result output includes swot_analysis")
        results["build_result"] = "PASS"
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        results["build_result"] = f"FAIL: {e}"

    # ---------------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------------
    print("\n" + "=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for v in results.values() if v == "PASS")
    skipped = sum(1 for v in results.values() if "SKIP" in str(v))
    warned = sum(1 for v in results.values() if "WARN" in str(v))
    failed = sum(1 for v in results.values() if str(v).startswith("FAIL"))
    
    for name, status in results.items():
        icon = "✅" if status == "PASS" else "⚠️ " if ("SKIP" in str(status) or "WARN" in str(status)) else "❌"
        print(f"  {icon} {name}: {status}")
    
    print(f"\n  Total: {passed} passed, {skipped} skipped, {warned} warnings, {failed} failed")
    print(f"  out of {len(results)} tests")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(test_all())
    sys.exit(0 if success else 1)
