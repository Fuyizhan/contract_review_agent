"""数据库 CRUD 操作。"""
from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import UserRecord, ReviewRecord, ClauseRecord
from sqlalchemy.orm import selectinload

# ==================== 用户相关 ====================

async def get_user_by_username(db: AsyncSession, username: str) -> UserRecord | None:
    """根据用户名查用户（登录时用）。"""
    result = await db.execute(select(UserRecord).where(UserRecord.username == username))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, username: str, password_hash: str) -> UserRecord:
    """创建新用户（注册时用）。"""
    user = UserRecord(username=username, hashed_password=password_hash)
    db.add(user)
    await db.flush() # 刷新以获取生成的 ID
    return user


# ==================== 审查记录相关 ====================

async def create_review(db: AsyncSession, user_id: str, filename: str, doc_path: str) -> ReviewRecord:
    """创建一条审查任务（上传文件后立刻调用）。"""
    review = ReviewRecord(
        user_id=user_id,
        original_filename=filename,
        document_path=doc_path,
        status="pending"
    )
    db.add(review)
    await db.flush()
    return review


async def get_review_by_id(db: AsyncSession, review_id: str) -> ReviewRecord | None:
    # 【修改这里】加上 .options(selectinload(ReviewRecord.clauses))
    stmt = (
        select(ReviewRecord)
        .options(selectinload(ReviewRecord.clauses))
        .where(ReviewRecord.id == review_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_review_progress(
    db: AsyncSession, review_id: str, status: str, progress: float
) -> None:
    """更新审查状态和进度（后台 AI 跑的时候用）。"""
    review = await get_review_by_id(db, review_id)
    if review:
        review.status = status
        review.progress = progress
        await db.flush()