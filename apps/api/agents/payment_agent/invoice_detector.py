from typing import Any

import logging
logger = logging.getLogger("agents.payment_agent.invoice_detector")


async def detect_invoice(email_body: str) -> dict[str, Any]:
    raise NotImplementedError("Payment Agent is not available in MVP. "
                              "Invoice detection will be implemented post-MVP.")


async def extract_invoice_number(text: str) -> str:
    raise NotImplementedError("Payment Agent is not available in MVP.")
