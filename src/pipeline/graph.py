
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Annotated
import operator
from src.agents.clause_extraction import ClauseExtractionAgent
from src.agents.risk_identification import RiskIdentificationAgent
from src.agents.compliance_check import ComplianceCheckAgent
from src.agents.suggestion import SuggestionAgent

#结点并行时 state：progress冲突 定义一个取最大值的合并函数
def keep_max(left: float, right: float) -> float:
    return max(left, right)

# 1. 定义共享状态（大托盘）
class ReviewState(TypedDict):
    review_id: str
    raw_text: str
    clauses: List[dict]
    risk_findings: List[dict]
    missing_clauses: List[dict]
    compliance_issues: List[dict]
    suggestions: List[dict]
    warnings: Annotated[List[str], operator.add]
    progress: Annotated[float, keep_max]

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

async def node_suggestion(state: ReviewState):
    return await suggestion_agent(state)

# 【新增】一个空的合并节点，用于汇聚并行结果
async def node_merge(state: ReviewState):
    print("-> [Merge] 风险与合规检查并行完成，准备生成建议...")
    return {"progress": 0.75}

# 4. 画图连线（开始 -> 提条款 -> 找风险 -> 结束）
builder = StateGraph(ReviewState)
builder.add_node("extract", node_extract_clauses)
builder.add_node("risk", node_identify_risks)
builder.add_node("compliance", node_compliance)
builder.add_node("merge", node_merge)       # 新增合并节点
builder.add_node("suggestion", node_suggestion) 

builder.set_entry_point("extract")
# 【核心改造】从 extract 引出两条边，变成并行！
builder.add_edge("extract", "risk")
builder.add_edge("extract", "compliance")
# 两个并行节点完成后，都指向 merge 节点进行合并
builder.add_edge("risk", "merge")
builder.add_edge("compliance", "merge")
# merge 汇聚后，再去生成建议
builder.add_edge("merge", "suggestion")
builder.add_edge("suggestion", END)

# 5. 编译
review_pipeline = builder.compile()