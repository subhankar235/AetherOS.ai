import uuid
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict

class MeetingBase(BaseModel):
    calendar_event_id: Optional[str] = None
    participants: list[dict[str, Any]] = []
    proposed_slots: list[dict[str, Any]] = []
    status: str = "previewed"

class MeetingCreate(MeetingBase):
    source_email_id: Optional[uuid.UUID] = None

class MeetingUpdate(BaseModel):
    calendar_event_id: Optional[str] = None
    participants: Optional[list[dict[str, Any]]] = None
    proposed_slots: Optional[list[dict[str, Any]]] = None
    status: Optional[str] = None

class MeetingResponse(MeetingBase):
    id: uuid.UUID
    user_id: str
    source_email_id: Optional[uuid.UUID]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
