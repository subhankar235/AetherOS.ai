import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base

class ConversationContext(Base):
    __tablename__ = "conversation_context"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    active_email_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("email_metadata.id", ondelete="SET NULL"), nullable=True)
    active_thread_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("threads.id", ondelete="SET NULL"), nullable=True)
    active_draft_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("drafts.id", ondelete="SET NULL"), nullable=True)
    last_search_query: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("user_id", "session_id", name="uq_user_session_context"),
    )
