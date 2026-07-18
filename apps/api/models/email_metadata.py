import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, UniqueConstraint, UUID, func
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base

class EmailMetadata(Base):
    __tablename__ = "email_metadata"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    gmail_message_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    thread_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("threads.id", ondelete="SET NULL"), nullable=True, index=True)
    sender: Mapped[str] = mapped_column(String, nullable=False)
    subject: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    priority: Mapped[str] = mapped_column(String, default="Medium", server_default="Medium")
    category: Mapped[str] = mapped_column(String, default="General", server_default="General")
    urgency: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    reply_required: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    suspicious_flag: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    indexed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "gmail_message_id", name="uq_user_gmail_message"),
    )
