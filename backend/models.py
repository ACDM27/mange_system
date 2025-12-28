from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base


class UserRole(str, enum.Enum):
    """User role enumeration"""
    STUDENT = "student"
    ADMIN = "admin"


class AchievementStatus(str, enum.Enum):
    """Achievement status enumeration"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class MessageRole(str, enum.Enum):
    """Chat message role enumeration"""
    USER = "user"
    ASSISTANT = "assistant"


class SysUser(Base):
    """System user table - login accounts"""
    __tablename__ = "sys_users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    avatar_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    student = relationship("SysStudent", back_populates="user", uselist=False)


class SysTeacher(Base):
    """Teacher basic data table"""
    __tablename__ = "sys_teachers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    title = Column(String(50))  # 职称
    department = Column(String(100))  # 院系
    
    # Relationships
    achievements = relationship("BizAchievement", back_populates="teacher")


class SysStudent(Base):
    """Student profile table"""
    __tablename__ = "sys_students"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("sys_users.id"), unique=True, nullable=False)
    student_number = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(50), nullable=False)
    major = Column(String(100))  # 专业
    persona_cache = Column(JSON)  # AI生成的画像数据
    
    # Relationships
    user = relationship("SysUser", back_populates="student")
    achievements = relationship("BizAchievement", back_populates="student")
    chat_sessions = relationship("AiChatSession", back_populates="student")


class BizAchievement(Base):
    """Achievement table"""
    __tablename__ = "biz_achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("sys_students.id"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("sys_teachers.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    type = Column(String(50), nullable=False)  # 字典值
    content_json = Column(JSON)  # OCR识别后的结构化详情
    evidence_url = Column(String(500))  # 证书图片地址
    status = Column(Enum(AchievementStatus), default=AchievementStatus.PENDING, index=True)
    audit_comment = Column(Text)  # 审核意见
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    student = relationship("SysStudent", back_populates="achievements")
    teacher = relationship("SysTeacher", back_populates="achievements")


class AiChatSession(Base):
    """AI chat session table"""
    __tablename__ = "ai_chat_sessions"
    
    id = Column(String(36), primary_key=True)  # UUID
    student_id = Column(Integer, ForeignKey("sys_students.id"), nullable=False, index=True)
    title = Column(String(200))  # 会话摘要
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = relationship("SysStudent", back_populates="chat_sessions")
    messages = relationship("AiChatMessage", back_populates="session", order_by="AiChatMessage.created_at")


class AiChatMessage(Base):
    """AI chat message table"""
    __tablename__ = "ai_chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), ForeignKey("ai_chat_sessions.id"), nullable=False, index=True)
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    session = relationship("AiChatSession", back_populates="messages")
