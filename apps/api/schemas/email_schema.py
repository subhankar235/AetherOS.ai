import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class EmailMetadataBase(BaseModel):
    gmail_message_id: str
    sender: str
    subject: str
    summary: Optional[str] = None
    priority: str = "Medium"
    category: str = "General"
    urgency: bool = False
    reply_required: bool = False
    suspicious_flag: bool = False
    received_at: datetime

class EmailMetadataCreate(EmailMetadataBase):
    thread_id: Optional[uuid.UUID] = None

class EmailMetadataUpdate(BaseModel):
    summary: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    urgency: Optional[bool] = None
    reply_required: Optional[bool] = None
    suspicious_flag: Optional[bool] = None

class EmailMetadataResponse(EmailMetadataBase):
    id: uuid.UUID
    user_id: uuid.UUID | str
    thread_id: Optional[uuid.UUID] = None
    indexed_at: datetime

    model_config = ConfigDict(from_attributes=True)
