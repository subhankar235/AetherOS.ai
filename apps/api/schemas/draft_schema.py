import uuid
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict

class DraftBase(BaseModel):
    current_body: str
    status: str = "drafting"

class DraftCreate(DraftBase):
    email_id: Optional[uuid.UUID] = None
    thread_id: Optional[uuid.UUID] = None

class DraftUpdate(BaseModel):
    current_body: Optional[str] = None
    status: Optional[str] = None
    version_history: Optional[list[dict[str, Any]]] = None

class DraftResponse(DraftBase):
    id: uuid.UUID
    user_id: str
    email_id: Optional[uuid.UUID]
    thread_id: Optional[uuid.UUID]
    version_history: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
