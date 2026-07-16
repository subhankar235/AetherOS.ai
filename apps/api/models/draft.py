import uuid
from datetime import datetime
from typing import Any, Optional
from sqlalchemy import String, DateTime, ForeignKey, UUID, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base

class Draft(Base):
    __tablename__ = "drafts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    email_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("email_metadata.id", ondelete="SET NULL"), nullable=True, index=True)
    thread_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("threads.id", ondelete="CASCADE"), nullable=True, index=True)
    current_body: Mapped[str] = mapped_column(String, nullable=False)
    version_history: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"))
    status: Mapped[str] = mapped_column(String, default="drafting", server_default="drafting")  # drafting | sent | discarded
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), server_default=func.now()
    )
