from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.deps import get_current_organization
from app.services.document_service import create_document, get_documents
from app.services.shared.file_storage import FileStorageService
from app.schemas.document import Document, DocumentCreate
from app.models.base import Organization

router = APIRouter()
storage = FileStorageService()

@router.get("/", response_model=List[Document])
def read_documents(db: Session = Depends(get_db), current_org: Organization = Depends(get_current_organization)):
    return get_documents(db, current_org.id)

@router.post("/", response_model=Document)
async def create_document_endpoint(
    name: str = Form(...), 
    category: str = Form(...), 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db), 
    current_org: Organization = Depends(get_current_organization)
):
    # Form data maps to DocumentCreate schema effectively for logic
    file_path = await storage.save_file(str(current_org.id), file)
    return create_document(db, name, category, file_path, current_org.id)
