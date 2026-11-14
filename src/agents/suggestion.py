from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.llm_utils import get_llm, structured_llm_call
from src.agents.schemas import SuggestionResult

SUGGESTION_PROMPT = """你是一个资深的企业法务顾问。
你的任务是根据之前的审查记录，为合同起草具体的修改建议和补充条款。

【输入信息】
你将收到：
1. 识别出的具体风险（risk_findings）
2. 缺失的必备条款（missing_clauses）
3. 存在的合规问题（compliance_issues）

【输出要求】
你必须只输出一个合法的 json 对象，不要包含任何 Markdown 标记。格式如下：
{
  "suggestions": [
    {
      "target": "针对哪个条款或问题",
      "issue": "简述问题",
      "suggestion": "提供具体的修改后的文本或补充条款",
      "priority": "high"
    }
  ]
}
请给出切实可行、符合中国法律规范的修改建议。"""

class SuggestionAgent:
    def __init__(self):
        self.llm = get_llm()

    async def __call__(self, state: dict) -> dict:
        print(f"-> [Agent 4] 正在生成修改建议...")
        
        risks = state.get("risk_findings", [])
        missing = state.get("missing_clauses", [])
        issues = state.get("compliance_issues", [])
        
        # 如果什么毛病都没挑出来，就不需要建议了
        if not risks and not missing and not issues:
            return {"suggestions": [], "progress": 1.0}

        # 把前面的结果打包成文本喂给大模型
        context = f"【风险】\n{risks}\n【缺失条款】\n{missing}\n【合规问题】\n{issues}"
        
        messages = [
            SystemMessage(content=SUGGESTION_PROMPT),
            HumanMessage(content=f"请根据以下审查结果生成修改建议：\n\n{context}")
        ]
        
        try:
            result = await structured_llm_call(self.llm, messages, SuggestionResult)
            suggestions_data = [s.model_dump() for s in result.suggestions]
            print(f"   ✅ 成功生成 {len(suggestions_data)} 条修改建议！")
            return {"suggestions": suggestions_data, "progress": 1.0}
        except Exception as e:
            print(f"   ❌ 生成建议失败: {e}")
            return {"suggestions": [], "progress": 1.0}