from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import Optional
from datetime import datetime
from database import get_db
from schemas import AchievementListResponse, AchievementResponse, AchievementAudit
from utils import success_response, error_response
from models import (
    BizAchievement, AchievementStatus, SysStudent,
    SysTeacher, SysUser
)
from dependencies import require_admin

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@router.get("/achievements")
async def get_achievements_for_review(
    status: Optional[str] = Query(None),
    student_name: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    admin: SysUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get achievements for review
    - Admin can view all achievements
    - Filter by status and student name
    - Pagination support
    """
    # Build query with joins
    query = db.query(BizAchievement).join(
        SysStudent, BizAchievement.student_id == SysStudent.id
    ).join(
        SysTeacher, BizAchievement.teacher_id == SysTeacher.id
    )
    
    # Apply filters
    if status:
        try:
            status_enum = AchievementStatus(status)
            query = query.filter(BizAchievement.status == status_enum)
        except ValueError:
            return error_response(msg="Invalid status value", code=400)
    
    if student_name:
        query = query.filter(SysStudent.name.like(f"%{student_name}%"))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    achievements = query.order_by(BizAchievement.created_at.desc()).offset(offset).limit(page_size).all()
    
    # Format response
    achievement_list = []
    for ach in achievements:
        achievement_list.append({
            "id": ach.id,
            "title": ach.title,
            "type": ach.type,
            "student_name": ach.student.name,
            "teacher_name": ach.teacher.name,
            "evidence_url": ach.evidence_url,
            "status": ach.status.value,
            "audit_comment": ach.audit_comment,
            "create_time": ach.created_at.isoformat(),
            "content_json": ach.content_json
        })
    
    return success_response(data={
        "list": achievement_list,
        "total": total
    })


@router.patch("/achievements/{achievement_id}/audit")
async def audit_achievement(
    achievement_id: int = Path(...),
    audit_req: AchievementAudit = None,
    admin: SysUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Audit achievement
    - Approve or reject achievement
    - Comment required for rejection
    - Invalidates student persona cache on approval
    """
    # Get achievement
    achievement = db.query(BizAchievement).filter(BizAchievement.id == achievement_id).first()
    
    if not achievement:
        return error_response(msg="Achievement not found", code=404)
    
    # Validate action
    if audit_req.action not in ["approve", "reject"]:
        return error_response(msg="Invalid action. Must be 'approve' or 'reject'", code=400)
    
    # Validate comment for rejection
    if audit_req.action == "reject" and not audit_req.comment:
        return error_response(msg="Comment is required for rejection", code=400)
    
    # Update achievement status
    if audit_req.action == "approve":
        achievement.status = AchievementStatus.APPROVED
        achievement.audit_comment = audit_req.comment or "Approved"
        
        # Invalidate persona cache for student
        student = db.query(SysStudent).filter(SysStudent.id == achievement.student_id).first()
        if student:
            student.persona_cache = None  # Mark for regeneration
    else:
        achievement.status = AchievementStatus.REJECTED
        achievement.audit_comment = audit_req.comment
    
    db.commit()
    
    # TODO: Send notification to student (optional)
    
    return success_response(msg=f"Achievement {audit_req.action}d successfully")
