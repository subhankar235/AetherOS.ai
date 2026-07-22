from typing import Any

import logging
logger = logging.getLogger("agents.payment_agent.fraud_checker")


async def check_fraud(payment_data: dict[str, Any]) -> dict[str, Any]:
    raise NotImplementedError("Payment Agent is not available in MVP. "
                              "Fraud checking will be implemented post-MVP.")
