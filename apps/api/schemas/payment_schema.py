import uuid
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict

class VendorBase(BaseModel):
    name: str
    org_id: Optional[str] = None

class VendorResponse(VendorBase):
    id: uuid.UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PurchaseOrderBase(BaseModel):
    po_number: str
    amount: float
    currency: str = "USD"
    status: str = "pending"
    org_id: Optional[str] = None

class PurchaseOrderResponse(PurchaseOrderBase):
    id: uuid.UUID
    user_id: Optional[str]
    vendor_id: uuid.UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PaymentPolicyBase(BaseModel):
    name: str
    rules: dict[str, Any] = {}
    org_id: Optional[str] = None

class PaymentPolicyResponse(PaymentPolicyBase):
    id: uuid.UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PaymentRecordBase(BaseModel):
    invoice_id: Optional[str] = None
    vendor: Optional[str] = None
    amount: float
    currency: str = "USD"
    policy_check_result: Optional[dict[str, Any]] = None
    approval_status: Optional[str] = None
    approved_by: Optional[str] = None
    executed_at: Optional[datetime] = None
    audit_ref: Optional[str] = None
    org_id: Optional[str] = None

class PaymentRecordResponse(PaymentRecordBase):
    id: uuid.UUID
    user_id: Optional[str]
    model_config = ConfigDict(from_attributes=True)
