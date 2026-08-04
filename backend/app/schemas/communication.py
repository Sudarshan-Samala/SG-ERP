from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class CommunicationBase(BaseModel):
    recipient_type: str # ALL, GRADE, BRANCH
    channel: str # SMS, EMAIL, WHATSAPP, IN_APP
    content: str

class CommunicationCreate(CommunicationBase):
    pass

class Communication(CommunicationBase):
    id: UUID
    organization_id: UUID
    status: str

    class Config:
        from_attributes = True
