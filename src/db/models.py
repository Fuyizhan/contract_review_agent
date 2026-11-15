"""核心数据库表定义（瘦身版）。"""
from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .session import Base

def gen_uuid() -> str:
    return str(uuid.uuid4())[:8]

class UserRecord(Base):
    """用户表"""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)


class ReviewRecord(Base):
    """审查报告主表"""
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), index=True) 
    status: Mapped[str] = mapped_column(String(20), default="pending") 
    original_filename: Mapped[str] = mapped_column(String(255)) 
    document_path: Mapped[str] = mapped_column(String(500)) 
    progress: Mapped[float] = mapped_column(Float, default=0.0) 
    
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)

    
    risk_findings: Mapped[list] = mapped_column(JSON, default=list)           # 风险
    
    # 合规检查结果（用这俩）
    missing_clauses: Mapped[list] = mapped_column(JSON, default=list)         # 缺失条款
    compliance_issues: Mapped[list] = mapped_column(JSON, default=list)       # 合规问题
    
    suggestions: Mapped[list] = mapped_column(JSON, default=list)             # 修改建议
    errors: Mapped[list] = mapped_column(JSON, default=list)                  # 运行报错
    warnings: Mapped[list] = mapped_column(JSON, default=list) 
    
    # 一对多关联：一份报告里有多个条款
    clauses: Mapped[list[ClauseRecord]] = relationship(back_populates="review", cascade="all, delete-orphan")


class ClauseRecord(Base):
    """条款表"""
    __tablename__ = "clauses"

    id: Mapped[str] = mapped_column(String(8), primary_key=True, default=gen_uuid)
    review_id: Mapped[str] = mapped_column(ForeignKey("reviews.id"))
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50), default="other") 
    review: Mapped[ReviewRecord] = relationship(back_populates="clauses")