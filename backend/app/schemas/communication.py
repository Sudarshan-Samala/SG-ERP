from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class CommunicationBase(BaseModel):
    recipient_type: Literal["ALL", "GRADE", "BRANCH"]
    channel: Literal["SMS", "EMAIL", "WHATSAPP", "IN_APP"]
    content: str = Field(min_length=1, max_length=5000)

    @field_validator("content")
    @classmethod
    def normalize_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("content must not be blank")
        return value

class CommunicationCreate(CommunicationBase):
    pass

class Communication(CommunicationBase):
    id: UUID
    organization_id: UUID
    status: Literal["DRAFT", "QUEUED", "SENT", "FAILED", "CANCELLED"]
    class Config:
        from_attributes = True
