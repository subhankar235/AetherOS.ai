from typing import Any

import logging
logger = logging.getLogger("agents.payment_agent.po_matcher")


async def match_purchase_order(invoice_data: dict[str, Any]) -> dict[str, Any]:
    raise NotImplementedError("Payment Agent is not available in MVP. "
                              "PO matching will be implemented post-MVP.")
