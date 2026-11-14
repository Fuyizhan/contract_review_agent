"""数据库连接与 Session 管理。"""
from __future__ import annotations
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from src.config import settings # 假设你的配置文件里有 settings.DATABASE_URL

# 1. 所有 ORM 模型的“老祖宗”
class Base(DeclarativeBase):
    pass

# 2. 全局占位，等应用启动时初始化
engine = None
async_session_factory: async_sessionmaker[AsyncSession] | None = None

def init_db(database_url: str) -> None:
    """初始化数据库引擎（应用启动时调用一次）。"""
    global engine, async_session_factory
    # echo=False 表示不在控制台疯狂打印 SQL；pool_pre_ping=True 防止连接断开
    engine = create_async_engine(database_url, echo=False, pool_pre_ping=True)
    async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖：每次请求分配一个独立的 Session。"""
    if async_session_factory is None:
        raise RuntimeError("数据库尚未初始化")
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit() # 请求成功，自动提交
        except Exception:
            await session.rollback() # 请求报错，自动回滚
            raise