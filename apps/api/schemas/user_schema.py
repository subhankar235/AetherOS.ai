from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr

class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    timezone: Optional[str] = None
    language_preference: str = "en"
    plan_tier: str = "free"

class UserCreate(UserBase):
    id: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    google_oauth_token: Optional[str] = None
    oauth_scopes: Optional[str] = None
    timezone: Optional[str] = None
    language_preference: Optional[str] = None
    plan_tier: Optional[str] = None

class UserResponse(UserBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
