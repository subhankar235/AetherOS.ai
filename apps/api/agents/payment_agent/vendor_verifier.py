from typing import Any

import logging
logger = logging.getLogger("agents.payment_agent.vendor_verifier")


async def verify_vendor(vendor_name: str, org_id: str) -> dict[str, Any]:
    raise NotImplementedError("Payment Agent is not available in MVP. "
                              "Vendor verification will be implemented post-MVP.")
