from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.llm_utils import get_llm, structured_llm_call
from src.agents.schemas import ClauseExtractResult

SYSTEM_PROMPT = """你是一个专业的法律合同条款提取专家。你的任务是从用户提供的合同文本中提取结构化的条款信息。

【重要要求】
1. 不要编造文本中不存在的内容，必须忠于原文。
2. 将合同文本切分为一个个独立的条款，尽量保留完整的上下文。
3. 提取每个条款时，必须对其进行分类（category）。

【分类标准】
只能使用以下分类代码：
- payment: 付款、价款、支付相关
- liability: 违约责任、赔偿、罚款相关
- confidentiality: 保密、商业秘密相关
- termination: 合同解除、终止、中止相关
- intellectual_property: 知识产权、专利、著作权归属相关
- other: 其他无法归入上述类别的条款
【输出格式】
你必须只输出一个合法的 json 对象，不要包含任何 Markdown 标记（如 ```json），格式如下：
{
  "contract_type": "合同类型，例如：技术服务合同",
  "clauses": [
    {
      "title": "条款标题",
      "content": "条款的完整正文",
      "category": "从分类标准中选择一个英文代码"
    }
  ]
}
"""

class ClauseExtractionAgent:
    def __init__(self):
        self.llm = get_llm()

    async def __call__(self, state: dict) -> dict:
        print(f"-> [Agent 1] 正在调用大模型提取条款...")
        
        # 拿原文（如果太长了，以后这里要加分块，现在先截取前 3000 字测试）
        raw_text = state.get("raw_text", "")[:3000] 
        if not raw_text:
            return {"clauses": [], "progress": 1.0}

        # 【核心】组装成标准的聊天消息列表
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"请提取以下合同文本中的条款信息：\n\n{raw_text}")
        ]
        
        try:
            # 真正调用大模型！把 schemas 里的 ClauseExtractResult 传进去
            result = await structured_llm_call(self.llm, messages, ClauseExtractResult)
            
            # 把大模型返回的 Pydantic 对象转成字典列表，方便存库
            clauses_data = [c.model_dump() for c in result.clauses]
            print(f"   ✅ 成功提取了 {len(clauses_data)} 条条款！类型：{result.contract_type}")
            return {"clauses": clauses_data, "progress": 0.25}
            
        except Exception as e:
            print(f"   ❌ 大模型提取失败: {e}")
            return {"clauses": [], "progress": 0.25}