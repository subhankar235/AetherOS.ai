import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class KnowledgeDocumentBase(BaseModel):
    title: str
    source_type: str  # upload | url
    file_path_or_url: str
    doc_type: str
    access_level: str = "Member"

class KnowledgeDocumentCreate(KnowledgeDocumentBase):
    org_id: Optional[str] = None

class KnowledgeDocumentUpdate(BaseModel):
    title: Optional[str] = None
    access_level: Optional[str] = None
    indexing_status: Optional[str] = None

class KnowledgeDocumentResponse(KnowledgeDocumentBase):
    id: uuid.UUID
    org_id: Optional[str]
    user_id: Optional[uuid.UUID]
    indexing_status: str
    uploaded_by: Optional[uuid.UUID]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
