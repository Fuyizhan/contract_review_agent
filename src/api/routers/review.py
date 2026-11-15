from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks, Response
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.schemas.review import TaskResponse, ReviewDetailResponse
from src.api.auth.dependencies import get_current_user
from src.db.session import get_db
import src.db.session as db_session
from src.db.models import UserRecord, ClauseRecord
from src.db.crud import create_review, get_review_by_id
from src.pipeline.graph import review_pipeline 
from src.services.report_service import generate_pdf_report
from src.services.document_parser import document_parser

router = APIRouter(prefix="/api/v1/review", tags=["Review"])

# ===== 后台任务：跑流水线 =====
async def run_review_pipeline_bg(review_id: str, raw_text: str):
    # 1. 初始化大托盘
    initial_state = {
        "review_id": review_id, 
        "raw_text": raw_text, 
        "clauses": [], 
        "risk_findings": [], 
        "missing_clauses": [], 
        "compliance_issues": [], 
        "suggestions": [],
        "warnings": [],
        "progress": 0.0
    }
    
    try:
        # 【核心改造】使用 astream 监听流水线的每一步
        async for event in review_pipeline.astream(initial_state):
            # event 的格式类似：{'extract': {'clauses': [...], 'progress': 0.5}}
            for node_name, state_update in event.items():
                # 只要节点返回了状态更新，立刻开独立 session 落库！
                async with db_session.async_session_factory() as db:
                    review = await get_review_by_id(db, review_id)
                    if review:
                        # 如果这个节点更新了 progress，存进去
                        if "progress" in state_update:
                            review.progress = state_update["progress"]
                        
                        # 如果流水线跑到了 suggestion（最后一个节点），把最终数据全存进去
                        if node_name == "suggestion":
                            review.status = "completed"
                            review.risk_findings = state_update.get("risk_findings", [])
                            review.missing_clauses = state_update.get("missing_clauses", [])
                            review.compliance_issues = state_update.get("compliance_issues", [])
                            review.suggestions = state_update.get("suggestions", [])
                            review.warnings = state_update.get("warnings", [])
                        
                        await db.commit()
                        print(f"💾 [进度落库] 节点 {node_name} 完成，当前进度: {review.progress}")

    except Exception as e:
        print(f"❌ [系统级崩溃] LangGraph 流水线执行发生严重错误: {e}")
        
        # 然后把库里的状态改成 failed
        async with db_session.async_session_factory() as db:
            review = await get_review_by_id(db, review_id)
            if review:
                review.status = "failed"
                review.errors = [f"系统内部错误: {str(e)}"]
                await db.commit()
            
            

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
    
    file_bytes = await file.read()

    content = await document_parser.parse(file_bytes, file.filename)
    
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

# ===== 下载 PDF 接口 =====
@router.get("/{review_id}/report")
async def download_report(
    review_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserRecord = Depends(get_current_user)
):
    review = await get_review_by_id(db, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="找不到审查记录")
        
    if review.status != "completed":
        raise HTTPException(status_code=400, detail="审查尚未完成，无法下载报告")
    
    # 组装数据
    report_data = {
        "original_filename": review.original_filename,
        "risk_findings": review.risk_findings,
        "missing_clauses": review.missing_clauses,
        "compliance_issues": review.compliance_issues,
        "suggestions": review.suggestions
    }

    # 生成 PDF
    pdf_bytes = generate_pdf_report(report_data)

    # 返回文件流
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_{review_id[:8]}.pdf"}
    )
