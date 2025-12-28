from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List
from datetime import datetime
from models import UserRole, AchievementStatus, MessageRole


# ============= Response Models =============
class ResponseModel(BaseModel):
    """Standard API response wrapper"""
    code: int = 200
    msg: str = "success"
    data: Optional[Any] = None


# ============= Auth Models =============
class LoginRequest(BaseModel):
    username: str
    password: str


class UserInfo(BaseModel):
    id: int
    name: str
    role: UserRole
    
    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    token: str
    userInfo: UserInfo


# ============= Teacher Models =============
class TeacherBase(BaseModel):
    name: str
    title: Optional[str] = None
    department: Optional[str] = None


class TeacherResponse(BaseModel):
    id: int
    name: str
    department: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============= Achievement Models =============
class AchievementCreate(BaseModel):
    title: str
    teacher_id: int
    type: str
    content_json: Optional[Dict] = None
    evidence_url: Optional[str] = None


class AchievementResponse(BaseModel):
    id: int
    title: str
    type: str
    content_json: Optional[Dict] = None
    evidence_url: Optional[str] = None
    status: AchievementStatus
    audit_comment: Optional[str] = None
    created_at: datetime
    student_name: Optional[str] = None
    teacher_name: Optional[str] = None
    create_time: Optional[str] = None
    
    class Config:
        from_attributes = True


class AchievementListResponse(BaseModel):
    list: List[AchievementResponse]
    total: int


class AchievementAudit(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$")
    comment: Optional[str] = None


# ============= OCR Models =============
class OCRResponse(BaseModel):
    title: str
    date: Optional[str] = None
    issuer: Optional[str] = None
    suggested_type: Optional[str] = None


# ============= Certificate Recognition Models =============
class CertificateRecognitionData(BaseModel):
    """Certificate data extracted by AI"""
    certificate_name: Optional[str] = None
    recipient_name: Optional[str] = None
    issuing_organization: Optional[str] = None
    issue_date: Optional[str] = None
    certificate_number: Optional[str] = None
    award_level: Optional[str] = None
    category: Optional[str] = None
    additional_info: Optional[str] = None
    recognition_time: Optional[str] = None
    model_used: Optional[str] = None
    confidence: Optional[str] = None


class CertificateRecognitionResponse(BaseModel):
    """Response from certificate recognition endpoint"""
    success: bool
    data: Optional[CertificateRecognitionData] = None
    file_url: Optional[str] = None  # Permanent URL of saved certificate
    error: Optional[str] = None


class AchievementCreateWithRecognition(BaseModel):
    """Create achievement using previously recognized certificate"""
    teacher_id: int
    certificate_url: str  # URL of previously saved and recognized certificate
    
    # Allow manual override of AI-recognized data
    title: Optional[str] = None
    type: Optional[str] = None
    content_json: Optional[Dict] = None


# ============= File Upload Models =============
class UploadResponse(BaseModel):
    url: str


# ============= AI Chat Models =============
class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    session_id: str
    message: str


# ============= Persona Models =============
class PersonaResponse(BaseModel):
    persona_data: Optional[Dict] = None
    last_updated: Optional[datetime] = None
