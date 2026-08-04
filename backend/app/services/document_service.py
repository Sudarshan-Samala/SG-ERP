from sqlalchemy.orm import Session
from app.models.base import Document
from uuid import UUID

def create_document(db: Session, name: str, category: str, file_path: str, organization_id: UUID):
    doc = Document(name=name, category=category, file_path=file_path, organization_id=organization_id)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

def get_documents(db: Session, organization_id: UUID):
    return db.query(Document).filter(Document.organization_id == organization_id).all()
