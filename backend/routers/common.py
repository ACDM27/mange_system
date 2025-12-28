from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
import aiofiles
from database import get_db
from schemas import TeacherResponse, UploadResponse
from utils import success_response, error_response
from models import SysTeacher
from dependencies import get_current_user
from config import settings

router = APIRouter(prefix="/api/v1/common", tags=["Common"])


@router.get("/teachers", response_model=List[TeacherResponse])
async def get_teachers(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get list of teachers for dropdown selection
    - Available to all authenticated users
    """
    teachers = db.query(SysTeacher).all()
    
    teacher_list = [
        {
            "id": t.id,
            "name": t.name,
            "department": t.department
        }
        for t in teachers
    ]
    
    return success_response(data=teacher_list)


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """
    File upload endpoint
    - Uploads file to local storage or OSS
    - Returns accessible URL
    """
    # Validate file size
    contents = await file.read()
    if len(contents) > settings.MAX_FILE_SIZE:
        return error_response(msg="File size exceeds maximum limit", code=400)
    
    # Reset file pointer
    await file.seek(0)
    
    # Create upload directory if not exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(contents)
    
    # Generate URL (in production, this would be an OSS URL)
    file_url = f"/uploads/{unique_filename}"
    
    return success_response(data={"url": file_url})
