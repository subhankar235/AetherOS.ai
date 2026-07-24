import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from schemas.agent_response_schema import AgentResponse
from voice.tone_adapter import (
    TONE_CALM_SERIOUS,
    TONE_CAREFUL_CLEAR,
    TONE_CASUAL_WARM,
    select_tone,
    get_voice_settings,
)
from voice.conversational_rewrite import rewrite


def test_tone_adapter_classification():
    # 1. Inbox summary / Triage -> casual_warm
    inbox_resp = AgentResponse(
        agent="triage_agent",
        status="completed",
        result={"items": [1, 2, 3, 4, 5], "total": 5, "high_priority_count": 2},
        requires_approval=False,
    )
    assert select_tone(inbox_resp) == TONE_CASUAL_WARM

    # 2. Approval Request -> careful_clear
    approval_resp = AgentResponse(
        agent="reply_agent",
        status="waiting_for_user",
        result={"draft_id": "draft_123", "recipient": "lokesh@example.com"},
        requires_approval=True,
    )
    assert select_tone(approval_resp) == TONE_CAREFUL_CLEAR

    # 3. Suspicious / Fraud Email -> calm_serious
    fraud_resp = AgentResponse(
        agent="triage_agent",
        status="completed",
        result={"sender": "hacker@phishing.com", "suspicious_flag": True, "reason": "Spoofed domain"},
        requires_approval=False,
    )
    assert select_tone(fraud_resp) == TONE_CALM_SERIOUS


def test_conversational_rewrite_inbox_summary_exit_criteria():
    inbox_resp = AgentResponse(
        agent="triage_agent",
        status="completed",
        result={"items": [1, 2, 3, 4, 5], "total": 5, "high_priority_count": 2},
        requires_approval=False,
    )
    output = rewrite(inbox_resp)

    # Must NOT read structured JSON or machine text verbatim
    assert "Query returned" not in output
    assert "total: 5" not in output
    assert "high_priority_count" not in output

    # Must match the natural spoken pattern
    assert "5 new emails" in output
    assert "2 look important" in output
    assert "want me to read those first?" in output


def test_conversational_rewrite_approval_guardrail_exit_criteria():
    draft_approval = AgentResponse(
        agent="reply_agent",
        status="waiting_for_user",
        result={"draft_id": "draft_456", "target_email": {"sender": "Lokesh"}},
        requires_approval=True,
    )
    output_draft = rewrite(draft_approval)
    assert "?" in output_draft
    assert any(kw in output_draft.lower() for kw in ["send", "approve", "confirm", "proceed", "would you like", "do you want"])

    calendar_approval = AgentResponse(
        agent="calendar_agent",
        status="waiting_for_user",
        result={"title": "Team Sync", "preview_id": "prev_789"},
        requires_approval=True,
    )
    output_cal = rewrite(calendar_approval)
    assert "?" in output_cal
    assert any(kw in output_cal.lower() for kw in ["schedule", "approve", "confirm", "proceed", "go ahead"])


def test_conversational_rewrite_suspicious_email_exit_criteria():
    suspicious_resp = AgentResponse(
        agent="inbox_agent",
        status="completed",
        result={
            "sender": "support@bank-fake-verify.com",
            "subject": "Account suspended",
            "suspicious_flag": True,
            "reason": "Phishing link detected",
        },
        requires_approval=False,
    )

    tone = select_tone(suspicious_resp)
    assert tone == TONE_CALM_SERIOUS

    voice_settings = get_voice_settings(tone)
    assert voice_settings["stability"] == 0.85
    assert voice_settings["style"] == 0.05

    output = rewrite(suspicious_resp, tone=tone)
    assert "support@bank-fake-verify.com" in output or "flagged" in output.lower()
    assert "caution" in output.lower() or "warning" in output.lower() or "phishing" in output.lower()
