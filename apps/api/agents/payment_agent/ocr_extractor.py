from typing import Any

import logging
logger = logging.getLogger("agents.payment_agent.ocr_extractor")


async def ocr_invoice(file_path: str) -> dict[str, Any]:
    raise NotImplementedError("Payment Agent is not available in MVP. "
                              "OCR extraction will be implemented post-MVP.")
