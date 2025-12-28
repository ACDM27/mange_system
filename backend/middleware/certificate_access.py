"""
Middleware for controlling access to certificate files
Only allows students to access their own certificates, or admins to access all
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from pathlib import Path
import re

from config import settings
from auth import decode_token
from database import SessionLocal
from models import SysUser, UserRole


class CertificateAccessMiddleware(BaseHTTPMiddleware):
    """Middleware to control access to certificate files"""
    
    async def dispatch(self, request: Request, call_next):
        # Check if request is for a certificate file
        if request.url.path.startswith("/uploads/certificates/"):
            # Extract student ID from path
            # Path format: /uploads/certificates/student_{id}/cert_xxx.jpg
            match = re.match(r"/uploads/certificates/student_(\d+)/", request.url.path)
            
            if not match:
                # Invalid path format
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Certificate not found"
                )
            
            file_owner_id = int(match.group(1))
            
            # Get authorization token
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                # No token - might be accessed from img tag, check cookie
                token = request.cookies.get("access_token")
                if not token:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required to access certificates"
                    )
            else:
                token = auth_header.replace("Bearer ", "")
            
            # Decode token and verify access
            try:
                payload = decode_token(token)
                username = payload.get("sub")
                
                if not username:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid token"
                    )
                
                # Get user from database
                db = SessionLocal()
                try:
                    user = db.query(SysUser).filter(SysUser.username == username).first()
                    
                    if not user:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="User not found"
                        )
                    
                    # Check access permissions
                    # Admin can access all certificates
                    if user.role == UserRole.ADMIN:
                        pass  # Allow access
                    # Student can only access their own certificates
                    elif user.role == UserRole.STUDENT:
                        if user.student and user.student.id == file_owner_id:
                            pass  # Allow access
                        else:
                            raise HTTPException(
                                status_code=status.HTTP_403_FORBIDDEN,
                                detail="Access denied: You can only access your own certificates"
                            )
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Access denied"
                        )
                        
                finally:
                    db.close()
                    
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Authentication failed: {str(e)}"
                )
        
        # Continue with request
        response = await call_next(request)
        return response
