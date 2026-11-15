from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.llm_utils import get_llm, structured_llm_call
from src.agents.schemas import ComplianceExtractResult

COMPLIANCE_PROMPT = """你是一个专业的合同合规审查专家。
你的任务是对给定的合同条款进行合规性检查。

【审查重点】
1. 必备条款是否缺失：一个标准的合同通常应包含（当事人信息、标的物、数量、质量、价款或报酬、履行期限、违约责任、争议解决方式）。
2. 强制性规定：条款内容是否违反了相关法律法规（如民法典中的强制性规定）。

【输出要求】
你必须只输出一个合法的 json 对象，不要包含任何 Markdown 标记。格式如下：
{
  "missing_clauses": ["违约责任", "争议解决方式"],
  "compliance_issues": ["本合同未约定管辖法院，可能存在合规隐患"]
}
如果各项都很完整合规，列表返回空即可。"""

class ComplianceCheckAgent:
    def __init__(self):
        self.llm = get_llm()

    async def __call__(self, state: dict) -> dict:
        print(f"-> [Agent 3] 正在调用大模型进行合规检查...")
        
        clauses = state.get("clauses", [])
        if not clauses:
            return {"missing_clauses": [], "compliance_issues": [], "progress": 0.75}

        # 把条款每 10 条分成一组，防止一次发太多
        batch_size = 10
        all_missing = []
        all_issues = []

        for i in range(0, len(clauses), batch_size):
            batch_clauses = clauses[i : i + batch_size]
            clauses_text = "\n".join([f"标题：{c['title']}\n内容：{c['content']}" for c in batch_clauses])
            
            messages = [
                SystemMessage(content=COMPLIANCE_PROMPT),
                HumanMessage(content=f"请检查以下合同条款的合规性（第 {i//batch_size + 1} 批）：\n\n{clauses_text}")
            ]
            
            try:
                result = await structured_llm_call(self.llm, messages, ComplianceExtractResult)
                all_missing.extend(result.missing_clauses)
                all_issues.extend(result.compliance_issues)
                print(f"   ✅ 第 {i//batch_size + 1} 批检查完成：缺失 {len(result.missing_clauses)} 项，合规问题 {len(result.compliance_issues)} 项")
            except Exception as e:
                print(f"   ❌ 第 {i//batch_size + 1} 批合规检查失败: {e}")

        # 去重处理（因为分批检查可能会出现重复的缺失项）
        all_missing = list(set(all_missing))
        all_issues = list(set(all_issues))

        print(f"   ✅ 合规检查全部完成！共缺失 {len(all_missing)} 项条款，发现 {len(all_issues)} 个合规问题！")
        return {
            "missing_clauses": all_missing, 
            "compliance_issues": all_issues, 
            "progress": 0.75
        }