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

class ComplianceExtractResult(BaseModel):
    missing_clauses: List[str] = Field(
        description="缺失的必备条款名称列表。如果没有缺失，返回空列表。"
    )
    compliance_issues: List[str] = Field(
        description="合同条款中违反法律法规的合规问题列表。"
    )

class SuggestionItem(BaseModel):
    target: str = Field(description="修改针对的目标，如：'第二条 违约金条款' 或 '缺失的保密条款'")
    issue: str = Field(description="存在的问题描述")
    suggestion: str = Field(description="具体的修改建议或补充条款内容")
    priority: str = Field(description="修改优先级：high/medium/low")

class SuggestionResult(BaseModel):
    suggestions: List[SuggestionItem] = Field(description="生成的修改建议列表")
