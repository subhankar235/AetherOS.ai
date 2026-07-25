"""
Tone Adapter module for Human Voice Layer (Phase 8.5).
Selects a deterministic tone profile based on AgentResponse properties.

Tones:
- casual_warm ("casual, warm"): Daily triage, inbox summaries, search results
- careful_clear ("careful, neutral, clear"): Approval requests (send/schedule/pay previews)
- calm_serious ("calm, serious"): Fraud/suspicious flagged emails or payment fraud warnings
"""

from typing import Any, Union
from schemas.agent_response_schema import AgentResponse

TONE_CASUAL_WARM = "casual_warm"
TONE_CAREFUL_CLEAR = "careful_clear"
TONE_CALM_SERIOUS = "calm_serious"

TONE_DESCRIPTIONS = {
    TONE_CASUAL_WARM: "casual, warm",
    TONE_CAREFUL_CLEAR: "careful, neutral, clear",
    TONE_CALM_SERIOUS: "calm, serious",
}

TONE_VOICE_SETTINGS = {
    TONE_CASUAL_WARM: {"stability": 0.35, "similarity_boost": 0.75, "style": 0.45},
    TONE_CAREFUL_CLEAR: {"stability": 0.75, "similarity_boost": 0.85, "style": 0.10},
    TONE_CALM_SERIOUS: {"stability": 0.85, "similarity_boost": 0.90, "style": 0.05},
}


def select_tone(response: Union[AgentResponse, dict[str, Any]]) -> str:
    if isinstance(response, AgentResponse):
        agent_name = response.agent
        requires_approval = response.requires_approval
        result = response.result or {}
    else:
        agent_name = response.get("agent", "")
        requires_approval = response.get("requires_approval", False)
        result = response.get("result", {})

    is_suspicious = (
        agent_name == "fraud_agent"
        or result.get("suspicious_flag", False)
        or result.get("is_suspicious", False)
        or result.get("fraud", False)
        or result.get("is_fraud", False)
        or "suspicious" in str(result).lower()
        or "fraud" in str(result).lower()
    )

    if is_suspicious:
        return TONE_CALM_SERIOUS

    if requires_approval or result.get("approval_required", False) or result.get("status") == "previewed":
        return TONE_CAREFUL_CLEAR

    return TONE_CASUAL_WARM


def get_voice_settings(tone: str) -> dict[str, float]:
    return TONE_VOICE_SETTINGS.get(tone, TONE_VOICE_SETTINGS[TONE_CASUAL_WARM])
