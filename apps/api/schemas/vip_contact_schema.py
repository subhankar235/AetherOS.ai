import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr

class VIPContactBase(BaseModel):
    contact_email: EmailStr
    contact_name: Optional[str] = None

class VIPContactCreate(VIPContactBase):
    pass

class VIPContactUpdate(BaseModel):
    contact_name: Optional[str] = None

class VIPContactResponse(VIPContactBase):
    id: uuid.UUID
    user_id: str
    added_at: datetime

    model_config = ConfigDict(from_attributes=True)
