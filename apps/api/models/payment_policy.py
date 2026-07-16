import uuid
from datetime import datetime
from typing import Any, Optional
from sqlalchemy import String, DateTime, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base

class PaymentPolicy(Base):
    __tablename__ = "payment_policies"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    org_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    rules: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), server_default=func.now())
