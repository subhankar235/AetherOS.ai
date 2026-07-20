from typing import Any

import logging
logger = logging.getLogger("agents.payment_agent.payment_summary")


async def generate_payment_summary(
    invoice_data: dict[str, Any],
    policy_result: dict[str, Any],
    fraud_result: dict[str, Any],
) -> dict[str, Any]:
    raise NotImplementedError("Payment Agent is not available in MVP. "
                              "Payment summary will be implemented post-MVP.")
