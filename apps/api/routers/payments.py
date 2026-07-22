import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.deps import get_current_user
from db.session import get_db
from models.user import User
from schemas.payment_schema import (
    PaymentRecordResponse,
    PaymentPolicyResponse,
    VendorResponse,
    PurchaseOrderResponse,
)

logger = logging.getLogger("routers.payments")

router = APIRouter(prefix="/payments", tags=["payments"])


def _check_enabled():
    if not settings.PAYMENT_AGENT_ENABLED:
        raise HTTPException(
            status_code=501,
            detail={
                "error": "Payment features are not available yet.",
                "message": "Payment processing will be available in a future release.",
                "code": "PAYMENT_AGENT_NOT_AVAILABLE",
            },
        )


@router.get("/status")
async def payment_status():
    return {
        "enabled": settings.PAYMENT_AGENT_ENABLED,
        "available": False,
        "message": "Payment processing is not available in the current version.",
    }


@router.post("/preview")
async def preview_payment(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _check_enabled()
    raise NotImplementedError("Payment preview is not yet implemented.")


@router.post("/execute")
async def execute_payment(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _check_enabled()
    raise NotImplementedError("Payment execution is not yet implemented.")


@router.get("/records", response_model=list[PaymentRecordResponse])
async def list_payment_records(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _check_enabled()
    return []


@router.get("/policies", response_model=list[PaymentPolicyResponse])
async def list_payment_policies(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _check_enabled()
    return []


@router.get("/vendors", response_model=list[VendorResponse])
async def list_vendors(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _check_enabled()
    return []


@router.get("/purchase-orders", response_model=list[PurchaseOrderResponse])
async def list_purchase_orders(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _check_enabled()
    return []
