from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.schemas.auth import LoginRequest, TokenResponse
from src.api.auth.security import verify_password, create_access_token
from src.db.session import get_db
from src.db.crud import get_user_by_username

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    # 1. 查用户
    user = await get_user_by_username(db, request.username)
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
        
    # 2. 发 Token
    token = create_access_token(subject=user.username, role="user")
    return TokenResponse(access_token=token)