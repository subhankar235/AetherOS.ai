import uuid
from datetime import datetime
from typing import Any, Optional
from sqlalchemy import String, Numeric, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base

class PaymentRecord(Base):
    __tablename__ = "payment_records"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    org_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    invoice_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    vendor: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String, default="USD", server_default="USD")
    policy_check_result: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    approval_status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    audit_ref: Mapped[Optional[str]] = mapped_column(String, nullable=True)
