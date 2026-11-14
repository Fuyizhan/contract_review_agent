from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session import get_db
from src.db.crud import get_user_by_username
from src.db.models import UserRecord
from .security import decode_access_token

# 自动从 Header 中提取 Bearer Token
bearer_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db)
) -> UserRecord:
    """获取当前登录用户。"""
    if not credentials:
        raise HTTPException(status_code=401, detail="未提供认证凭据")
    
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="无效或过期的 Token")
    
    username = payload.get("sub")
    user = await get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return user