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
            return {"risk_findings": [], "progress": 1.0}

        # 把提取出来的条款拼成一段文本，准备放进 HumanMessage
        clauses_text = "\n".join([f"【类别：{c.get('category', 'other')}】\n标题：{c['title']}\n内容：{c['content']}" for c in clauses])

        # 【核心改造】组装标准的聊天消息列表
        messages = [
            SystemMessage(content=RISK_PROMPT),
            HumanMessage(content=(
                "请审查以下合同条款，并找出风险点：\n\n" + 
                # 如果你还没写 wrap_untrusted，可以直接用 clauses_text
                clauses_text
            ))
        ]
        
        try:
            # 传入消息列表进行结构化调用
            result = await structured_llm_call(self.llm, messages, RiskIdentifyResult)
            
            # 把 Pydantic 对象转成字典列表，方便存库
            risks_data = [r.model_dump() for r in result.risk_findings]
            print(f"   ✅ 发现 {len(risks_data)} 个风险点！")
            return {"risk_findings": risks_data, "progress": 0.5}
            
        except Exception as e:
            print(f"   ❌ 风险分析失败: {e}")
            return {"risk_findings": [], "progress": 1.0}