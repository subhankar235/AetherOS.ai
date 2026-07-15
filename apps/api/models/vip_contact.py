import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base

class VIPContact(Base):
    __tablename__ = "vip_contacts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_email: Mapped[str] = mapped_column(String, nullable=False, index=True)
    contact_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "contact_email", name="uq_user_vip_contact_email"),
    )
