"""
File Management Service
Handles permanent storage and access control for certificate files
"""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException
from config import settings


class FileManager:
    """Service for managing certificate file storage"""
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.certificates_dir = self.upload_dir / "certificates"
        self.temp_certificates_dir = self.upload_dir / "temp_certificates"
        
        # Create directories if they don't exist
        self.certificates_dir.mkdir(parents=True, exist_ok=True)
        self.temp_certificates_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_student_certificate_dir(self, student_id: int) -> Path:
        """Get the certificate directory for a specific student"""
        student_dir = self.certificates_dir / f"student_{student_id}"
        student_dir.mkdir(parents=True, exist_ok=True)
        return student_dir
    
    def _generate_certificate_filename(self, student_id: int, original_filename: str) -> str:
        """
        Generate a unique filename for certificate
        Format: cert_{student_id}_{timestamp}_{random}.{ext}
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = str(uuid.uuid4())[:8]
        file_extension = Path(original_filename).suffix.lower()
        
        return f"cert_{student_id}_{timestamp}_{random_suffix}{file_extension}"
    
    async def save_certificate_permanent(
        self, 
        file: UploadFile, 
        student_id: int
    ) -> dict:
        """
        Save certificate file permanently for a student
        
        Args:
            file: Uploaded file
            student_id: Student ID
            
        Returns:
            Dictionary containing file path and URL
        """
        # Validate file extension
        allowed_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".pdf"]
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Validate file size
        if len(file_content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum of {settings.MAX_FILE_SIZE} bytes"
            )
        
        # Generate filename and get directory
        filename = self._generate_certificate_filename(student_id, file.filename)
        student_dir = self._get_student_certificate_dir(student_id)
        file_path = student_dir / filename
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Generate relative URL (accessible via static file mount)
        relative_path = file_path.relative_to(self.upload_dir)
        file_url = f"/uploads/{relative_path.as_posix()}"
        
        return {
            "file_path": str(file_path),
            "file_url": file_url,
            "filename": filename,
            "original_filename": file.filename,
            "size_bytes": len(file_content)
        }
    
    def verify_certificate_access(
        self, 
        file_path: str, 
        student_id: int,
        is_admin: bool = False
    ) -> bool:
        """
        Verify if a student has access to a certificate file
        
        Args:
            file_path: Path or URL to the certificate
            student_id: Student ID requesting access
            is_admin: Whether the requester is admin
            
        Returns:
            True if access is allowed
        """
        # Admin has access to all files
        if is_admin:
            return True
        
        # Convert URL to path if needed
        if file_path.startswith("/uploads/"):
            file_path = file_path.replace("/uploads/", "")
        
        # Check if file belongs to student's directory
        expected_prefix = f"certificates/student_{student_id}/"
        
        return file_path.startswith(expected_prefix)
    
    def get_certificate_full_path(self, file_url: str) -> Optional[Path]:
        """
        Convert file URL to full file system path
        
        Args:
            file_url: URL like /uploads/certificates/student_1/cert_xxx.jpg
            
        Returns:
            Full Path object or None if invalid
        """
        if not file_url.startswith("/uploads/"):
            return None
        
        # Remove /uploads/ prefix
        relative_path = file_url.replace("/uploads/", "")
        full_path = self.upload_dir / relative_path
        
        # Verify file exists
        if not full_path.exists() or not full_path.is_file():
            return None
        
        # Security check: ensure path is within upload directory
        try:
            full_path.resolve().relative_to(self.upload_dir.resolve())
        except ValueError:
            # Path is outside upload directory - security violation
            return None
        
        return full_path
    
    def delete_certificate(self, file_url: str, student_id: int, is_admin: bool = False) -> bool:
        """
        Delete a certificate file
        
        Args:
            file_url: URL of the file to delete
            student_id: Student ID requesting deletion
            is_admin: Whether requester is admin
            
        Returns:
            True if deleted successfully
        """
        # Verify access
        if not self.verify_certificate_access(file_url, student_id, is_admin):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get full path
        file_path = self.get_certificate_full_path(file_url)
        if not file_path:
            return False
        
        # Delete file
        try:
            os.remove(file_path)
            return True
        except Exception:
            return False
    
    def cleanup_temp_certificates(self, max_age_hours: int = 24):
        """
        Clean up temporary certificate files older than specified hours
        
        Args:
            max_age_hours: Maximum age in hours before deletion
        """
        now = datetime.now()
        count = 0
        
        for temp_file in self.temp_certificates_dir.iterdir():
            if temp_file.is_file():
                # Check file age
                file_age = now - datetime.fromtimestamp(temp_file.stat().st_mtime)
                if file_age.total_seconds() > (max_age_hours * 3600):
                    try:
                        os.remove(temp_file)
                        count += 1
                    except Exception:
                        pass
        
        return count
    
    def get_student_certificates(self, student_id: int) -> list:
        """
        Get list of all certificates for a student
        
        Args:
            student_id: Student ID
            
        Returns:
            List of certificate file info
        """
        student_dir = self._get_student_certificate_dir(student_id)
        certificates = []
        
        for cert_file in student_dir.iterdir():
            if cert_file.is_file():
                relative_path = cert_file.relative_to(self.upload_dir)
                certificates.append({
                    "filename": cert_file.name,
                    "url": f"/uploads/{relative_path.as_posix()}",
                    "size_bytes": cert_file.stat().st_size,
                    "created_at": datetime.fromtimestamp(cert_file.stat().st_ctime).isoformat()
                })
        
        return certificates


# Create singleton instance
file_manager = FileManager()
