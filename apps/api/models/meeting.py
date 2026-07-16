import uuid
from datetime import datetime
from typing import Any, Optional
from sqlalchemy import String, DateTime, ForeignKey, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base

class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_email_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("email_metadata.id", ondelete="SET NULL"), nullable=True, index=True)
    calendar_event_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    participants: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"))
    proposed_slots: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"))
    status: Mapped[str] = mapped_column(String, default="previewed", server_default="previewed")  # previewed | confirmed | cancelled
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), server_default=func.now())
