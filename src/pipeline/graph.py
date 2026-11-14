from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from src.agents.clause_extraction import ClauseExtractionAgent
from src.agents.risk_identification import RiskIdentificationAgent

# 1. 定义共享状态（大托盘）
class ReviewState(TypedDict):
    review_id: str
    raw_text: str
    clauses: List[dict]
    risk_findings: List[dict]
    progress: float

# 2. 实例化两个 Agent
clause_agent = ClauseExtractionAgent()
risk_agent = RiskIdentificationAgent()

# 3. 定义 LangGraph 的节点（把它们包成函数）
async def node_extract_clauses(state: ReviewState):
    return await clause_agent(state)

async def node_identify_risks(state: ReviewState):
    return await risk_agent(state)

# 4. 画图连线（开始 -> 提条款 -> 找风险 -> 结束）
builder = StateGraph(ReviewState)
builder.add_node("extract", node_extract_clauses)
builder.add_node("risk", node_identify_risks)

builder.set_entry_point("extract")
builder.add_edge("extract", "risk")
builder.add_edge("risk", END)

# 5. 编译
review_pipeline = builder.compile()