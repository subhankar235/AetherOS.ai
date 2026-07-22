import logging

from core.celery_app import celery_app

logger = logging.getLogger("workers.invoice_scanner")


@celery_app.task(name="workers.invoice_scanner.scan_invoices")
def scan_invoices() -> dict:
    raise NotImplementedError(
        "Invoice scanner is not available in MVP. "
        "It will be implemented when the Payment Agent (Phase 17) ships."
    )
