import uuid
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict

class PlaybookBase(BaseModel):
    name: str
    scenario_type: str
    template_structure: str
    tone_settings: Optional[dict[str, Any]] = None

class PlaybookCreate(PlaybookBase):
    org_id: Optional[str] = None

class PlaybookUpdate(BaseModel):
    name: Optional[str] = None
    scenario_type: Optional[str] = None
    template_structure: Optional[str] = None
    tone_settings: Optional[dict[str, Any]] = None
    org_id: Optional[str] = None

class PlaybookResponse(PlaybookBase):
    id: uuid.UUID
    user_id: Optional[str]
    org_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
