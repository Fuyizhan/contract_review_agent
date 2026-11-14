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

        clauses_text = "\n".join([f"标题：{c['title']}\n内容：{c['content']}" for c in clauses])
        
        messages = [
            SystemMessage(content=COMPLIANCE_PROMPT),
            HumanMessage(content=f"请检查以下合同条款的合规性：\n\n{clauses_text}")
        ]
        
        try:
            result = await structured_llm_call(self.llm, messages, ComplianceExtractResult)
            print(f"   ✅ 合规检查完成！缺失条款：{len(result.missing_clauses)}，合规问题：{len(result.compliance_issues)}")
            return {
                "missing_clauses": result.missing_clauses,
                "compliance_issues": result.compliance_issues,
                "progress": 0.75
            }
        except Exception as e:
            print(f"   ❌ 合规检查失败: {e}")
            return {"missing_clauses": [], "compliance_issues": [], "progress": 0.75}