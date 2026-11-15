from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.config import settings
import src.db.session as db_session  # 只导入模块，不导入具体变量
from src.db import models
from src.api.routers import auth, review
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. 启动：连库、建表、插入一个测试管理员账号（方便登录）
    db_session.init_db(settings.DATABASE_URL)
    async with db_session.engine.begin() as conn:
        await conn.run_sync(db_session.Base.metadata.create_all)
        
    # 临时塞一个 admin/admin123 账号
    async with db_session.async_session_factory() as db:
        from src.api.auth.security import get_password_hash
        from src.db.crud import get_user_by_username, create_user
        if not await get_user_by_username(db, "admin"):
            await create_user(db, "admin", get_password_hash("admin123"))
            await db.commit()
            
    yield
    await db_session.engine.dispose()

app = FastAPI(title="合同审查系统", lifespan=lifespan)

# 【新增：配置跨域】
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], # 允许前端的地址
    allow_credentials=True,
    allow_methods=["*"], # 允许所有方法 (GET, POST)
    allow_headers=["*"], # 允许所有请求头 (比如 Authorization)
)

# 挂载路由
app.include_router(auth.router)
app.include_router(review.router)