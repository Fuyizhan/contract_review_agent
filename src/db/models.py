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
    user_id: Mapped[str] = mapped_column(String(36), index=True) # 关联用户
    status: Mapped[str] = mapped_column(String(20), default="pending") # pending, in_progress, completed, failed
    original_filename: Mapped[str] = mapped_column(String(255)) # 文件名
    document_path: Mapped[str] = mapped_column(String(500)) # 文件存硬盘的路径，不存全文，省空间！
    progress: Mapped[float] = mapped_column(Float, default=0.0) # 进度 0.0 - 1.0
    
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)

    # 【神来之笔】把风险、合规、建议统统塞进 JSON 字段，前端拿到直接解析渲染，不需要复杂的连表查询
    overall_risk_level: Mapped[str] = mapped_column(String(10), default="none")
    risk_findings: Mapped[list] = mapped_column(JSON, default=list)
    compliance_findings: Mapped[list] = mapped_column(JSON, default=list)
    suggestions: Mapped[list] = mapped_column(JSON, default=list)
    errors: Mapped[list] = mapped_column(JSON, default=list) # 记录过程中的报错

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