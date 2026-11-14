# src/agents/schemas.py
from pydantic import BaseModel, Field
from typing import List

# 1. 条款结构
class Clause(BaseModel):
    title: str = Field(description="条款标题，如：第一条 服务内容")
    content: str = Field(description="条款的完整正文")
    category: str = Field(
        default="other",
        description="条款类别，只能从以下选择：payment(付款), liability(违约/责任), confidentiality(保密), termination(终止), intellectual_property(知识产权), other(其他)"
    )

# 2. 条款提取 Agent 的整体输出结果
class ClauseExtractResult(BaseModel):
    contract_type: str = Field(description="识别出的合同类型，如：技术服务合同、劳动合同等")
    clauses: List[Clause] = Field(description="提取出的所有条款列表")

# 3. 风险结构
class RiskFinding(BaseModel):
    risk_level: str = Field(description="风险等级：high/medium/low")
    description: str = Field(description="风险描述")

# 4. 风险识别 Agent 的整体输出结果
class RiskIdentifyResult(BaseModel):
    risk_findings: List[RiskFinding] = Field(description="提取出的所有风险列表")

# 【补上这个：合规检查】
class ComplianceFinding(BaseModel):
    status: str = Field(description="合规状态：compliant(合规) / non_compliant(不合规)")
    issue: str = Field(description="违规点或需要注意的问题")

class Suggestion(BaseModel):
    original_text: str = Field(description="原条款内容")
    suggested_text: str = Field(description="修改后的建议")
    reason: str = Field(description="修改理由")

# 最终 Agent 要输出的完整结构（四大金刚齐全了）
class AnalysisResult(BaseModel):
    clauses: List[Clause] = Field(default_factory=list)
    risk_findings: List[RiskFinding] = Field(default_factory=list)
    compliance_findings: List[ComplianceFinding] = Field(default_factory=list)
    suggestions: List[Suggestion] = Field(default_factory=list)