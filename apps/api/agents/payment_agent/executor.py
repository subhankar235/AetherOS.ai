from typing import Any

import logging
logger = logging.getLogger("agents.payment_agent.executor")


async def preview_payment(payment_data: dict[str, Any]) -> dict[str, Any]:
    raise NotImplementedError("Payment Agent is not available in MVP. "
                              "Payment preview will be implemented post-MVP.")


async def execute_payment(preview_id: str, approval_id: str) -> dict[str, Any]:
    raise NotImplementedError("Payment Agent is not available in MVP. "
                              "Payment execution will be implemented post-MVP.")
