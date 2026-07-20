from typing import Any

import logging
logger = logging.getLogger("agents.payment_agent.policy_validator")


async def validate_against_policy(payment_data: dict[str, Any], org_id: str) -> dict[str, Any]:
    raise NotImplementedError("Payment Agent is not available in MVP. "
                              "Policy validation will be implemented post-MVP.")


async def get_applicable_policies(org_id: str) -> list[dict[str, Any]]:
    raise NotImplementedError("Payment Agent is not available in MVP.")
