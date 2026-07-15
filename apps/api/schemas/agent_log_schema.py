import uuid
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict

class AgentLogBase(BaseModel):
    agent_name: str
    action_type: str
    input_payload: Optional[dict[str, Any]] = None
    output_payload: Optional[dict[str, Any]] = None
    requires_approval: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    status: str = "completed"

class AgentLogCreate(AgentLogBase):
    pass

class AgentLogUpdate(BaseModel):
    output_payload: Optional[dict[str, Any]] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    status: Optional[str] = None

class AgentLogResponse(AgentLogBase):
    id: uuid.UUID
    user_id: str

    model_config = ConfigDict(from_attributes=True)
