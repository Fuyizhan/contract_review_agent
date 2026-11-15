# src/agents/risk_identification.py
from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.llm_utils import get_llm, structured_llm_call
from src.agents.schemas import RiskIdentifyResult

RISK_PROMPT = """你是一个严格的企业法务风控专家。
你的任务是审查给定的合同条款，找出可能对己方不利、存在法律合规风险或表述模糊的条款。

【审查重点】
1. 金额与付款条件是否合理（如：违约金比例是否畸高）。
2. 责任划分是否公平（如：是否存在单方面免责的霸王条款）。
3. 关键条款是否缺失保护（如：没有明确的争议解决方式）。
4. 对于 liability（违约/责任）和 payment（付款）类条款，请重点审查其金额比例、付款节点和违约后果是否公平合理。

如果条款完全合法合规且公平，请不要强行编造风险，返回空列表即可。

【输出格式】
你必须只输出一个合法的 json 对象，不要包含任何 Markdown 标记（如 ```json），格式如下：
{
  "risk_findings": [
    {
      "risk_level": "high",
      "description": "具体的风险描述，说明为什么存在风险"
    }
  ]
}
"""

class RiskIdentificationAgent:
    def __init__(self):
        self.llm = get_llm()

    async def __call__(self, state: dict) -> dict:
        print(f"-> [Agent 2] 正在调用大模型分析风险...")
        
        clauses = state.get("clauses", [])
        if not clauses:
            return {"risk_findings": [], "progress": 0.5}

        # 把条款每 10 条分成一组，防止一次发太多
        batch_size = 10
        all_risks = []

        for i in range(0, len(clauses), batch_size):
            batch_clauses = clauses[i : i + batch_size]
            clauses_text = "\n".join([f"【类别：{c.get('category', 'other')}】\n标题：{c['title']}\n内容：{c['content']}" for c in batch_clauses])
            
            messages = [
                SystemMessage(content=RISK_PROMPT),
                HumanMessage(content=f"请审查以下合同条款（第 {i//batch_size + 1} 批）：\n\n{clauses_text}")
            ]
            
            try:
                result = await structured_llm_call(self.llm, messages, RiskIdentifyResult)
                all_risks.extend([r.model_dump() for r in result.risk_findings])
                print(f"   ✅ 第 {i//batch_size + 1} 批发现 {len(result.risk_findings)} 个风险")
            except Exception as e:
                print(f"   ❌ 第 {i//batch_size + 1} 批风险分析失败: {e}")

        # 【新增：在这里进行按严重程度排序】
        risk_weights = {"high": 3, "medium": 2, "low": 1}
        all_risks.sort(
            key=lambda x: risk_weights.get(x.get("risk_level", "low").lower(), 0), 
            reverse=True
        )
        print(f"   ✅ 风险识别全部完成！总共发现 {len(all_risks)} 个风险点！")
        return {"risk_findings": all_risks, "progress": 0.5}

        