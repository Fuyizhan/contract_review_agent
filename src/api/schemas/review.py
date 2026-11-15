# src/api/schemas/review.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

# 前端上传文件后，后端立刻返回的格式
class TaskResponse(BaseModel):
    review_id: str
    status: str
    message: str = "任务已提交"

class ClauseResponse(BaseModel):
    id: str
    title: str
    content: str
    category: str

    model_config = {"from_attributes": True} # 允许从 ORM 转换

# 查进度时，返回的格式
class ReviewDetailResponse(BaseModel):
    review_id: str = Field(validation_alias="id")
    status: str
    progress: float
    original_filename: str
    overall_risk_level: str = "none"
    created_at: datetime

    # 因为大模型抽取的数据结构复杂，这里直接用 list 或 dict 接收
    risk_findings: List[dict] = []
    missing_clauses: List[str] = []
    compliance_issues: List[str] = [] 
    suggestions: List[dict] = []
    warnings: List[str] = []
    # 返回真实的关系子表数据
    clauses: List[ClauseResponse] = [] 

    # 告诉 Pydantic：即使这个数据是从数据库的 ORM 对象里拿出来的，也能直接转
    model_config = {"from_attributes": True}