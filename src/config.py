"""全局配置管理。"""
from __future__ import annotations

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ---------------------------------------------------------
    # 数据库配置
    # ---------------------------------------------------------
    # 默认值设置为本地 SQLite（方便你测试），如果 .env 里配置了 PostgreSQL，就会覆盖它
    DATABASE_URL: str = "sqlite+aiosqlite:///./contract_review.db"

    # ---------------------------------------------------------
    # 安全与认证配置
    # ---------------------------------------------------------
    # 用于 JWT 签名的密钥（生产环境必须用随机长字符串）
    JWT_SECRET_KEY: str = "your-super-secret-key-change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # Token 过期时间，默认 1 天

    # ---------------------------------------------------------
    # 大模型配置 (可选)
    # ---------------------------------------------------------
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.deepseek.com"
    LLM_MODEL: str = "deepseek-chat"

    # ---------------------------------------------------------
    # 应用基础配置
    # ---------------------------------------------------------
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    
    # 上传目录
    UPLOAD_DIR: str = "./uploads"

    # 告诉 Pydantic Settings 去读取项目根目录下的 .env 文件
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore" # 忽略 .env 里多余的变量
    )


# 实例化一个全局单例，以后所有地方都直接 from src.config import settings 即可
settings = Settings()