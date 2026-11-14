from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.schemas.review import TaskResponse, ReviewDetailResponse
from src.api.auth.dependencies import get_current_user
from src.db.session import get_db
import src.db.session as db_session
from src.db.models import UserRecord, ClauseRecord
from src.db.crud import create_review, get_review_by_id
from src.pipeline.graph import review_pipeline 

router = APIRouter(prefix="/api/v1/review", tags=["Review"])

# ===== 后台任务：跑流水线 =====
async def run_review_pipeline_bg(review_id: str, raw_text: str):
    # 1. 初始化大托盘
    initial_state = {
        "review_id": review_id, 
        "raw_text": raw_text, 
        "clauses": [], 
        "risk_findings": [], 
        "progress": 0.0
    }
    
    # 2. 让 LangGraph 开始流转
    final_state = await review_pipeline.ainvoke(initial_state)
    
    # 3. 结果落库
    async with db_session.async_session_factory() as db:
        review = await get_review_by_id(db, review_id)
        if review:
            review.status = "completed"
            review.progress = 1.0
            review.risk_findings = final_state.get("risk_findings", [])
            
            # 【新增：处理条款子表】
            clauses_data = final_state.get("clauses", [])
            
            # 1. 为了防止重复，先删掉这个审查记录之前的旧条款（虽然第一次跑没旧的，但为了严谨）
            from sqlalchemy import delete
            await db.execute(delete(ClauseRecord).where(ClauseRecord.review_id == review.id))
            
            # 2. 把大模型提取的新条款，遍历插进子表
            for c in clauses_data:
                new_clause = ClauseRecord(
                    review_id=review.id,
                    title=c.get("title", "未命名"),
                    content=c.get("content", ""),
                    # 如果你的 ClauseRecord 里有 category 字段，就加上：
                    category=c.get("category", "other") 
                )
                db.add(new_clause)

            # 3. 提交事务
            await db.commit()
            print(f"✅ 流水线跑完，数据已入库: {review_id}，保存了 {len(clauses_data)} 条条款和{len(review.risk_findings)}风险。")

# ===== 上传接口 =====
@router.post("/upload", response_model=TaskResponse)
async def upload_review(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserRecord = Depends(get_current_user)
):
    # 1. 建数据库记录（pending）
    doc_path = f"/tmp/{file.filename}"
    review = await create_review(db, user_id=current_user.id, filename=file.filename, doc_path=doc_path)
    await db.commit() 
    
    content = (await file.read()).decode("utf-8", errors="ignore")
    
    # 2. 把任务扔到后台，立刻返回
    background_tasks.add_task(run_review_pipeline_bg, review.id, content)
    
    return TaskResponse(review_id=review.id, status="pending")

# ===== 查进度接口 =====
@router.get("/{review_id}", response_model=ReviewDetailResponse)
async def get_review(
    review_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserRecord = Depends(get_current_user)
):
    review = await get_review_by_id(db, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="找不到审查记录")
    return review