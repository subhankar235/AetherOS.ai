import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint, UUID, func
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base

class Thread(Base):
    __tablename__ = "threads"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    gmail_thread_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    thread_summary: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("user_id", "gmail_thread_id", name="uq_user_gmail_thread"),
    )
