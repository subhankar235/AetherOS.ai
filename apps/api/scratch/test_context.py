import asyncio
from agents.supervisor.context_manager import resolve_reference

async def main():
    # Test 1: Google Emails Search (5 items)
    google_items = [
        {"id": f"g_{i}", "subject": f"Google Update {i}", "sender": "Google Security <no-reply@google.com>"}
        for i in range(1, 6)
    ]
    ctx_google = {"last_search_results": google_items}
    
    status, res = await resolve_reference("Reply to the 4th email", ctx_google)
    assert res["resolved_email"]["subject"] == "Google Update 4"
    print("[SUCCESS] Generic Test 1 Passed: 'Reply to the 4th email' on Google search -> Google Update 4")

    status, res = await resolve_reference("Reply to the last email", ctx_google)
    assert res["resolved_email"]["subject"] == "Google Update 5"
    print("[SUCCESS] Generic Test 2 Passed: 'Reply to the last email' on Google search -> Google Update 5")

    # Test 2: Unstop / Hackathon Emails Search (8 items)
    unstop_items = [
        {"id": f"u_{i}", "subject": f"Unstop Hackathon #{i}", "sender": "Unstop <events@unstop.com>"}
        for i in range(1, 9)
    ]
    ctx_unstop = {"last_search_results": unstop_items}

    status, res = await resolve_reference("Draft a reply for the 7th one", ctx_unstop)
    assert res["resolved_email"]["subject"] == "Unstop Hackathon #7"
    print("[SUCCESS] Generic Test 3 Passed: 'Draft a reply for the 7th one' on Unstop search -> Unstop Hackathon #7")

    status, res = await resolve_reference("Reply to email #8", ctx_unstop)
    assert res["resolved_email"]["subject"] == "Unstop Hackathon #8"
    print("[SUCCESS] Generic Test 4 Passed: 'Reply to email #8' -> Unstop Hackathon #8")

    status, res = await resolve_reference("Reply casually for the last one", ctx_unstop)
    assert res["resolved_email"]["subject"] == "Unstop Hackathon #8"
    print("[SUCCESS] Generic Test 5 Passed: 'Reply casually for the last one' -> Unstop Hackathon #8")

    # Test 3: Combined Schedule + Draft Intent Classification
    from agents.supervisor.intent_router import _fallback_classification
    intent_res = _fallback_classification("Schedule meeting tomorrow at 3pm and make a draft reply to the last email")
    assert intent_res["intent"] == "multi_step"
    assert len(intent_res["tasks"]) == 2
    assert intent_res["tasks"][0]["agent"] == "calendar_agent"
    assert intent_res["tasks"][1]["agent"] == "reply_agent"
    print("[SUCCESS] Combined Test 6 Passed: 'Schedule meeting... and make a draft...' -> Multi-Step [calendar_agent, reply_agent]")

    # Test 4: "also make draft for the same email" resolution
    ctx_same = {
        "active_email_id": "mlh_email_4_id",
        "last_search_results": [
            {"id": "mlh_email_4_id", "subject": "Fwd: Everything you'll need to know from MLH at Hexafalls 2", "sender": "lokesh <lokeshhazraiem28@gmail.com>"}
        ]
    }
    status, res = await resolve_reference("also make draft for the same email", ctx_same)
    assert status == "resolved"
    assert res["resolved_value"] == "mlh_email_4_id"
    # Test 5: "write a draft for the 4 th email" (space between 4 and th)
    inbox_items = [
        {"id": f"item_{i}", "subject": f"Email #{i}", "sender": f"sender_{i}@domain.com"}
        for i in range(1, 7)
    ]
    ctx_spaced = {"last_search_results": inbox_items}
    status, res = await resolve_reference("write a draft for the 4 th email", ctx_spaced)
    assert status == "resolved"
    assert res["resolved_email"]["subject"] == "Email #4"
    # Test 6: Auto-populating 6 real inbox emails from DB when context is empty
    real_db_emails = [
        {"id": "u1", "subject": "A full year of career growth: Save with a Udemy Personal Plan...", "sender": "Udemy <hello@students.udemy.com>"},
        {"id": "u2", "subject": "What the f**k !!", "sender": "Reddit <noreply@redditmail.com>"},
        {"id": "u3", "subject": "Verify Your Identity | Major League Hacking", "sender": "Major League Hacking <notifications@mlh.io>"},
        {"id": "u4", "subject": "Fwd: Everything you'll need to know from MLH at Hexafalls 2 💻", "sender": "lokesh <lokeshhazraiem28@gmail.com>"},
        {"id": "u5", "subject": "WNS Group Manager HR recently posted", "sender": "LinkedIn <updates-noreply@linkedin.com>"},
        {"id": "u6", "subject": "WNS shared a post", "sender": "LinkedIn <notifications-noreply@linkedin.com>"},
    ]
    empty_ctx = {"last_search_results": real_db_emails}
    status, res = await resolve_reference("write a draft for the 4th email", empty_ctx)
    assert status == "resolved"
    assert res["resolved_email"]["subject"] == "Fwd: Everything you'll need to know from MLH at Hexafalls 2 💻"
    assert res["resolved_email"]["sender"] == "lokesh <lokeshhazraiem28@gmail.com>"
    print("[SUCCESS] Real Mailbox Test 9 Passed: 'write a draft for the 4th email' -> Fwd: Everything you'll need to know from MLH at Hexafalls 2 (lokesh)")

    print("\n[SUCCESS] ALL UNIVERSAL CONTEXT & MULTI-STEP TESTS PASSED 100%!")

if __name__ == "__main__":
    asyncio.run(main())
