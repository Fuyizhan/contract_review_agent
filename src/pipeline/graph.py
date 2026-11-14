from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from src.agents.clause_extraction import ClauseExtractionAgent
from src.agents.risk_identification import RiskIdentificationAgent
from src.agents.compliance_check import ComplianceCheckAgent
from src.agents.suggestion import SuggestionAgent

# 1. 定义共享状态（大托盘）
class ReviewState(TypedDict):
    review_id: str
    raw_text: str
    clauses: List[dict]
    risk_findings: List[dict]
    missing_clauses: List[dict]
    compliance_issues: List[dict]
    suggestions: List[dict]
    progress: float

# 2. 实例化两个 Agent
clause_agent = ClauseExtractionAgent()
risk_agent = RiskIdentificationAgent()
compliance_agent = ComplianceCheckAgent()
suggestion_agent = SuggestionAgent()

# 3. 定义 LangGraph 的节点（把它们包成函数）
async def node_extract_clauses(state: ReviewState):
    return await clause_agent(state)

async def node_identify_risks(state: ReviewState):
    return await risk_agent(state)

async def node_compliance(state: ReviewState):
    return await compliance_agent(state)

async def node_generate_suggestions(state: ReviewState):
    return await suggestion_agent(state)

# 4. 画图连线（开始 -> 提条款 -> 找风险 -> 结束）
builder = StateGraph(ReviewState)
builder.add_node("extract", node_extract_clauses)
builder.add_node("risk", node_identify_risks)
builder.add_node("compliance", node_compliance)
builder.add_node("suggestions", node_generate_suggestions)

builder.set_entry_point("extract")
builder.add_edge("extract", "risk")
builder.add_edge("risk", "compliance")
builder.add_edge("compliance", "suggestions")
builder.add_edge("suggestions", END)

# 5. 编译
review_pipeline = builder.compile()