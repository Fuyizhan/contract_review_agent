from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.llm_utils import get_llm, structured_llm_call
from src.agents.schemas import SuggestionResult
from src.rules.engine import generate_suggestions_fallback

SUGGESTION_PROMPT = """你是一个资深的企业法务顾问。
你的任务是根据之前的审查记录，为合同起草具体的修改建议和补充条款。

【输入信息】
你将收到：
1. 识别出的具体风险（risk_findings）
2. 缺失的必备条款（missing_clauses）
3. 存在的合规问题（compliance_issues）

【重要规则】
- 生成的 `suggestion.priority` 必须与它对应的【风险等级】或【合规严重度】保持一致！
  （例如：针对 high 级风险提出的修改建议，其 priority 必须也是 high）。
- 请针对给定的问题给出具体的修改建议，不要长篇大论。

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

        all_suggestions = []
        degrade_warnings = []
        
        # 1. 处理风险（每 5 个风险分一批，因为生成建议的 Prompt 比较长）
        batch_size = 10
        for i in range(0, len(risks), batch_size):
            batch_risks = risks[i : i + batch_size]
            context = f"【需要修改的风险】\n{batch_risks}\n"
            
            messages = [
                SystemMessage(content=SUGGESTION_PROMPT),
                HumanMessage(content=f"请根据以下风险生成修改建议（第 {i//batch_size + 1} 批）：\n\n{context}")
            ]
            
            try:
                result = await structured_llm_call(self.llm, messages, SuggestionResult)
                all_suggestions.extend([s.model_dump() for s in result.suggestions])
                print(f"   ✅ 第 {i//batch_size + 1} 批风险建议生成完成")
            except Exception as e:
                print(f"   ⚠️ [降级触发] 第 {i//batch_size + 1} 批大模型失败，启用模板兜底: {e}")
                fallback_sugs = generate_suggestions_fallback(batch_risks)
                all_suggestions.extend(fallback_sugs)
                
                degrade_warnings.append(f"修改建议第 {i//batch_size + 1} 批降级：大模型不可用。")
                continue # 继续下一批

        # 2. 处理缺失条款和合规问题（如果没传给风险 Agent 的话）
        # 简单起见，可以合并成一批处理
        if missing or issues:
            context = f"【缺失条款】\n{missing}\n\n【合规问题】\n{issues}\n"
            messages = [
                SystemMessage(content=SUGGESTION_PROMPT),
                HumanMessage(content=f"请根据以下合规问题生成修改建议：\n\n{context}")
            ]
            try:
                result = await structured_llm_call(self.llm, messages, SuggestionResult)
                all_suggestions.extend([s.model_dump() for s in result.suggestions])
                print(f"   ✅ 合规与缺失条款建议生成完成")
            except Exception as e:
                print(f"   ⚠️ [降级触发] 合规建议大模型失败，跳过模板生成: {e}")
                # 如果这部分挂了，一般不用强求兜底，记录警告即可
                degrade_warnings.append("合规与缺失条款建议生成降级：大模型不可用。")

        # 3. 【核心排序】把生成的所有建议，按优先级重新排序
        priority_weights = {"high": 3, "medium": 2, "low": 1}
        all_suggestions.sort(
            key=lambda x: priority_weights.get(x.get("priority", "low").lower(), 0), 
            reverse=True
        )

        print(f"   ✅ 共生成 {len(all_suggestions)} 条修改建议，已按优先级排序！")
        return {"suggestions": all_suggestions, 
                "warnings": state.get("warnings", []) + degrade_warnings,
                "progress": 1.0}