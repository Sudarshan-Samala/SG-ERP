import os
from fastapi import UploadFile
from app.core.config import settings

class FileStorageService:
    def __init__(self, base_path: str = "storage"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    async def save_file(self, organization_id: str, file: UploadFile) -> str:
        org_path = os.path.join(self.base_path, organization_id)
        os.makedirs(org_path, exist_ok=True)
        file_path = os.path.join(org_path, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        return file_path
