import enum
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Enum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class UserRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # The ONLY link to identity. Never store Google tokens on this table —
    # those live in google_integrations (Phase 6), keyed off this id.
    clerk_user_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)

    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String, nullable=True)

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.MEMBER, nullable=False
    )

    timezone: Mapped[str] = mapped_column(String, default="UTC", nullable=False)
    language_preference: Mapped[str] = mapped_column(String, default="en", nullable=False)
    plan_tier: Mapped[str] = mapped_column(String, default="free", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

