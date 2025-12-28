from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from schemas import LoginRequest, LoginResponse, UserInfo
from utils import success_response, error_response
from models import SysUser, UserRole
from auth import verify_password, create_access_token

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    User login endpoint
    - Validates username and password
    - Returns JWT token and user info
    """
    # Find user
    user = db.query(SysUser).filter(SysUser.username == request.username).first()
    
    if not user or not verify_password(request.password, user.password_hash):
        return error_response(msg="Invalid username or password", code=401)
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value}
    )
    
    # Prepare user info
    user_name = user.username
    if user.role == UserRole.STUDENT and user.student:
        user_name = user.student.name
    
    user_info = UserInfo(
        id=user.id,
        name=user_name,
        role=user.role
    )
    
    response_data = LoginResponse(
        token=access_token,
        userInfo=user_info
    )
    
    return success_response(data=response_data.model_dump())
