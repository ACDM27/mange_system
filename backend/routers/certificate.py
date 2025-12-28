"""
Certificate Recognition Router
Provides API endpoints for certificate recognition using AI
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List, Dict
import os
import uuid
from datetime import datetime

from config import settings
from services.certificate_recognition import certificate_recognition_service
from dependencies import get_current_user
from models import SysUser

router = APIRouter(
    prefix="/api/certificate",
    tags=["Certificate Recognition"]
)


@router.post("/recognize", response_model=Dict)
async def recognize_certificate(
    file: UploadFile = File(...),
    current_user: SysUser = Depends(get_current_user)
):
    """
    Recognize a certificate image and extract structured information
    
    **Permission**: Authenticated users (students/admins)
    
    **Request Body**:
    - file: Certificate image file (JPEG, PNG, etc.)
    
    **Response**:
    - success: Whether recognition was successful
    - data: Extracted certificate information
        - certificate_name: Name of the certificate/award
        - recipient_name: Name of the recipient
        - issuing_organization: Organization that issued the certificate
        - issue_date: Date when certificate was issued (YYYY-MM-DD)
        - certificate_number: Certificate number (if available)
        - award_level: Award level (if applicable)
        - category: Category of the award
        - additional_info: Any additional information
        - recognition_time: When the recognition was performed
        - model_used: AI model used for recognition
        - confidence: Confidence level of recognition
    """
    # Validate file type
    allowed_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".gif"]
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Check file size
    file_content = await file.read()
    if len(file_content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE} bytes"
        )
    
    # Save file temporarily
    temp_dir = os.path.join(settings.UPLOAD_DIR, "temp_certificates")
    os.makedirs(temp_dir, exist_ok=True)
    
    temp_filename = f"{uuid.uuid4()}{file_extension}"
    temp_filepath = os.path.join(temp_dir, temp_filename)
    
    try:
        # Write file to disk
        with open(temp_filepath, "wb") as f:
            f.write(file_content)
        
        # Recognize certificate
        result = await certificate_recognition_service.recognize_certificate(temp_filepath)
        
        # Validate result
        validated_result = certificate_recognition_service.validate_recognition_result(result)
        
        return validated_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing certificate: {str(e)}")
    
    finally:
        # Clean up temporary file
        if os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
            except:
                pass


@router.post("/batch-recognize", response_model=Dict)
async def batch_recognize_certificates(
    files: List[UploadFile] = File(...),
    current_user: SysUser = Depends(get_current_user)
):
    """
    Batch recognize multiple certificate images
    
    **Permission**: Authenticated users (students/admins)
    
    **Request Body**:
    - files: List of certificate image files
    
    **Response**:
    - success: Whether batch recognition was successful
    - results: List of recognition results for each file
    - total: Total number of files processed
    - successful: Number of successfully recognized certificates
    - failed: Number of failed recognitions
    """
    # Validate number of files
    max_batch_size = 10
    if len(files) > max_batch_size:
        raise HTTPException(
            status_code=400,
            detail=f"Batch size exceeds maximum of {max_batch_size} files"
        )
    
    temp_dir = os.path.join(settings.UPLOAD_DIR, "temp_certificates")
    os.makedirs(temp_dir, exist_ok=True)
    
    temp_files = []
    results = []
    
    try:
        # Save all files temporarily
        for file in files:
            # Validate file type
            allowed_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".gif"]
            file_extension = os.path.splitext(file.filename)[1].lower()
            
            if file_extension not in allowed_extensions:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": f"Invalid file type: {file_extension}"
                })
                continue
            
            # Check file size
            file_content = await file.read()
            if len(file_content) > settings.MAX_FILE_SIZE:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": "File size exceeds maximum"
                })
                continue
            
            # Save file
            temp_filename = f"{uuid.uuid4()}{file_extension}"
            temp_filepath = os.path.join(temp_dir, temp_filename)
            
            with open(temp_filepath, "wb") as f:
                f.write(file_content)
            
            temp_files.append({
                "filepath": temp_filepath,
                "original_filename": file.filename
            })
        
        # Recognize all certificates
        for temp_file in temp_files:
            try:
                result = await certificate_recognition_service.recognize_certificate(
                    temp_file["filepath"]
                )
                validated_result = certificate_recognition_service.validate_recognition_result(result)
                
                results.append({
                    "filename": temp_file["original_filename"],
                    **validated_result
                })
            except Exception as e:
                results.append({
                    "filename": temp_file["original_filename"],
                    "success": False,
                    "error": str(e)
                })
        
        # Calculate statistics
        successful = sum(1 for r in results if r.get("success"))
        failed = len(results) - successful
        
        return {
            "success": True,
            "results": results,
            "total": len(results),
            "successful": successful,
            "failed": failed
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in batch processing: {str(e)}")
    
    finally:
        # Clean up all temporary files
        for temp_file in temp_files:
            if os.path.exists(temp_file["filepath"]):
                try:
                    os.remove(temp_file["filepath"])
                except:
                    pass


@router.get("/health")
async def certificate_recognition_health():
    """
    Check if certificate recognition service is configured and ready
    
    **Response**:
    - status: Service status
    - configured: Whether API key is configured
    - model: Model name being used
    """
    is_configured = bool(settings.QWEN_API_KEY and settings.QWEN_API_KEY != "")
    
    return {
        "status": "ready" if is_configured else "not_configured",
        "configured": is_configured,
        "model": settings.QWEN_MODEL_NAME if is_configured else None,
        "message": "Certificate recognition service is ready" if is_configured else "API key not configured"
    }
