import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ConversationContextBase(BaseModel):
    session_id: str
    active_email_id: Optional[uuid.UUID] = None
    active_thread_id: Optional[uuid.UUID] = None
    active_draft_id: Optional[uuid.UUID] = None
    last_search_query: Optional[str] = None

class ConversationContextCreate(ConversationContextBase):
    pass

class ConversationContextUpdate(BaseModel):
    active_email_id: Optional[uuid.UUID] = None
    active_thread_id: Optional[uuid.UUID] = None
    active_draft_id: Optional[uuid.UUID] = None
    last_search_query: Optional[str] = None

class ConversationContextResponse(ConversationContextBase):
    id: uuid.UUID
    user_id: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
