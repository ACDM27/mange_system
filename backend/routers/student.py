from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import uuid
import httpx
from datetime import datetime, timedelta
from database import get_db
from schemas import (
    OCRResponse, AchievementCreate, AchievementResponse,
    ChatRequest, ChatResponse, PersonaResponse
)
from utils import success_response, error_response
from models import (
    SysStudent, BizAchievement, AchievementStatus,
    AiChatSession, AiChatMessage, MessageRole, SysTeacher
)
from dependencies import require_student
from config import settings

router = APIRouter(prefix="/api/v1/student", tags=["Student"])


@router.post("/ocr/recognize")
async def ocr_recognize(
    file: UploadFile = File(...),
    student: SysStudent = Depends(require_student)
):
    """
    Certificate recognition with permanent storage (Step 1 of 2)
    - Accepts certificate image
    - Saves file permanently to student's directory
    - Calls AI vision model for extraction
    - Returns structured data + file URL
    - User can then confirm and submit achievement in Step 2
    """
    from services.file_manager import file_manager
    from services.certificate_recognition import certificate_recognition_service
    
    try:
        # Step 1: Save certificate permanently
        file_info = await file_manager.save_certificate_permanent(file, student.id)
        
        # Step 2: Recognize certificate using AI
        recognition_result = await certificate_recognition_service.recognize_certificate(
            file_info["file_path"]
        )
        
        # Step 3: Validate and return result
        if recognition_result.get("success"):
            data = recognition_result.get("data", {})
            
            return success_response(data={
                "recognized_data": {
                    "title": data.get("certificate_name"),
                    "date": data.get("issue_date"),
                    "issuer": data.get("issuing_organization"),
                    "suggested_type": data.get("category"),
                    "award_level": data.get("award_level"),
                    "certificate_number": data.get("certificate_number"),
                    "recipient_name": data.get("recipient_name"),
                    "additional_info": data.get("additional_info"),
                },
                "file_url": file_info["file_url"],
                "file_info": {
                    "filename": file_info["filename"],
                    "original_filename": file_info["original_filename"],
                    "size_bytes": file_info["size_bytes"]
                },
                "ai_metadata": {
                    "model_used": data.get("model_used"),
                    "recognition_time": data.get("recognition_time"),
                    "confidence": data.get("confidence")
                }
            })
        else:
            # Recognition failed, but file is still saved
            return error_response(
                msg=f"Certificate saved but recognition failed: {recognition_result.get('error')}",
                code=500,
                data={
                    "file_url": file_info["file_url"],
                    "recognized_data": None
                }
            )
            
    except HTTPException as e:
        raise e
    except Exception as e:
        return error_response(msg=f"Error processing certificate: {str(e)}", code=500)


@router.post("/achievements")
async def create_achievement(
    achievement: AchievementCreate,
    student: SysStudent = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Submit achievement (Step 2 of 2)
    - Creates new achievement record
    - Status defaults to 'pending'
    - Must select existing teacher
    - If evidence_url is provided, verifies student has access to that certificate
    """
    from services.file_manager import file_manager
    
    # Validate teacher exists
    teacher = db.query(SysTeacher).filter(SysTeacher.id == achievement.teacher_id).first()
    if not teacher:
        return error_response(msg="Teacher not found", code=404)
    
    # If evidence_url is provided, verify access
    if achievement.evidence_url:
        if not file_manager.verify_certificate_access(
            achievement.evidence_url, 
            student.id, 
            is_admin=False
        ):
            return error_response(
                msg="Access denied: You can only use your own certificates",
                code=403
            )
    
    # Create achievement
    new_achievement = BizAchievement(
        student_id=student.id,
        teacher_id=achievement.teacher_id,
        title=achievement.title,
        type=achievement.type,
        content_json=achievement.content_json,
        evidence_url=achievement.evidence_url,
        status=AchievementStatus.PENDING
    )
    
    db.add(new_achievement)
    db.commit()
    db.refresh(new_achievement)
    
    return success_response(data={"id": new_achievement.id}, msg="Achievement submitted successfully")


@router.get("/achievements")
async def get_my_achievements(
    status: Optional[str] = Query(None),
    student: SysStudent = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Get my achievements
    - Returns only current student's achievements
    - Optional filter by status
    """
    query = db.query(BizAchievement).filter(BizAchievement.student_id == student.id)
    
    if status:
        try:
            status_enum = AchievementStatus(status)
            query = query.filter(BizAchievement.status == status_enum)
        except ValueError:
            return error_response(msg="Invalid status value", code=400)
    
    achievements = query.order_by(BizAchievement.created_at.desc()).all()
    
    achievement_list = []
    for ach in achievements:
        achievement_list.append({
            "id": ach.id,
            "title": ach.title,
            "type": ach.type,
            "content_json": ach.content_json,
            "evidence_url": ach.evidence_url,
            "status": ach.status.value,
            "audit_comment": ach.audit_comment,
            "created_at": ach.created_at.isoformat(),
            "teacher_name": ach.teacher.name if ach.teacher else None
        })
    
    return success_response(data=achievement_list)


@router.get("/certificates")
async def get_my_certificates(
    student: SysStudent = Depends(require_student)
):
    """
    Get list of my certificates
    - Returns all certificate files uploaded by current student
    - Files are stored in student-specific directory
    """
    from services.file_manager import file_manager
    
    certificates = file_manager.get_student_certificates(student.id)
    
    return success_response(data={
        "certificates": certificates,
        "total": len(certificates)
    })


@router.get("/persona")
async def get_persona(
    student: SysStudent = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    Get student persona
    - Checks cache validity
    - Regenerates if expired (async task in production)
    - Returns AI-generated persona data
    """
    # Check if persona cache exists and is valid
    # For demo, consider cache valid for 7 days
    needs_regeneration = False
    
    if not student.persona_cache:
        needs_regeneration = True
    
    # TODO: Implement actual persona generation using LLM
    # This would analyze approved achievements and chat history
    # For now, return cached data or mock data
    
    if needs_regeneration:
        # Mock persona generation
        # In production, this would be an async task
        persona_data = {
            "strengths": ["数学建模", "创新能力"],
            "achievements_summary": "参与多项竞赛并获奖",
            "suggested_improvements": ["加强英语能力", "拓展跨学科知识"],
            "generated_at": datetime.utcnow().isoformat()
        }
        
        student.persona_cache = persona_data
        db.commit()
    else:
        persona_data = student.persona_cache
    
    return success_response(data=persona_data)


@router.post("/ai/chat")
async def ai_chat(
    chat_req: ChatRequest,
    student: SysStudent = Depends(require_student),
    db: Session = Depends(get_db)
):
    """
    AI chat with context management
    - Backend manages conversation history
    - Implements RAG with student achievements
    - Stores messages in database
    """
    # Get or create session
    session_id = chat_req.session_id
    
    if not session_id:
        # Create new session
        session_id = str(uuid.uuid4())
        new_session = AiChatSession(
            id=session_id,
            student_id=student.id,
            title=chat_req.message[:50]  # Use first 50 chars as title
        )
        db.add(new_session)
        db.commit()
    else:
        # Validate session belongs to student
        session = db.query(AiChatSession).filter(
            AiChatSession.id == session_id,
            AiChatSession.student_id == student.id
        ).first()
        
        if not session:
            return error_response(msg="Session not found", code=404)
    
    # Store user message
    user_message = AiChatMessage(
        session_id=session_id,
        role=MessageRole.USER,
        content=chat_req.message
    )
    db.add(user_message)
    db.commit()
    
    # Retrieve chat history (last 10 messages)
    history = db.query(AiChatMessage).filter(
        AiChatMessage.session_id == session_id
    ).order_by(AiChatMessage.created_at.desc()).limit(10).all()
    history.reverse()  # Oldest first
    
    # Retrieve approved achievements for RAG
    achievements = db.query(BizAchievement).filter(
        BizAchievement.student_id == student.id,
        BizAchievement.status == AchievementStatus.APPROVED
    ).all()
    
    # Build context for LLM
    achievements_context = "\n".join([
        f"- {ach.title} ({ach.type})" for ach in achievements
    ])
    
    history_context = "\n".join([
        f"{msg.role.value}: {msg.content}" for msg in history[:-1]  # Exclude current message
    ])
    
    # TODO: Call actual LLM API
    # This is a mock response - replace with actual API call
    # Example:
    # async with httpx.AsyncClient() as client:
    #     response = await client.post(
    #         settings.LLM_API_URL,
    #         json={
    #             "model": "gpt-4",
    #             "messages": [
    #                 {"role": "system", "content": f"你是一位学业导师。学生的成果：\n{achievements_context}"},
    #                 {"role": "user", "content": chat_req.message}
    #             ]
    #         },
    #         headers={"Authorization": f"Bearer {settings.LLM_API_KEY}"}
    #     )
    #     ai_response = response.json()["choices"][0]["message"]["content"]
    
    # Mock AI response
    ai_response = f"根据你的成果记录，我看到你在{achievements[0].type if achievements else '多个领域'}有不错的表现。关于你的问题：{chat_req.message}，我建议..."
    
    # Store AI response
    assistant_message = AiChatMessage(
        session_id=session_id,
        role=MessageRole.ASSISTANT,
        content=ai_response
    )
    db.add(assistant_message)
    
    # Update session timestamp
    session = db.query(AiChatSession).filter(AiChatSession.id == session_id).first()
    session.updated_at = datetime.utcnow()
    
    db.commit()
    
    return success_response(data={
        "session_id": session_id,
        "message": ai_response
    })
