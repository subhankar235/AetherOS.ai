import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ThreadBase(BaseModel):
    gmail_thread_id: str
    thread_summary: Optional[str] = None

class ThreadCreate(ThreadBase):
    pass

class ThreadUpdate(BaseModel):
    thread_summary: Optional[str] = None

class ThreadResponse(ThreadBase):
    id: uuid.UUID
    user_id: str
    last_updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
