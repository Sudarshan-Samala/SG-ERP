from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class DocumentBase(BaseModel):
    name: str
    category: str # POLICY, CERTIFICATE, CONTRACT

class DocumentCreate(DocumentBase):
    pass

class Document(DocumentBase):
    id: UUID
    organization_id: UUID
    file_path: str

    class Config:
        from_attributes = True
