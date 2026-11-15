from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.llm_utils import get_llm, structured_llm_call
from src.agents.schemas import ClauseExtractResult
from src.agents.chunking import chunk_text

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
        raw_text = state.get("raw_text", "")
        if not raw_text:
            return {"clauses": [], "progress": 0.0}

         # 先分块
        text_chunks = chunk_text(raw_text, max_chars=3000, overlap=200)
        print(f"   合同过长，已切分为 {len(text_chunks)} 个文本块进行处理。")

        all_clauses = []
        contract_type = "未知"

        # 【修改点 2】循环调用大模型
        for i, chunk in enumerate(text_chunks):
            prompt = f"请提取以下合同文本中的条款信息（第 {i+1}/{len(text_chunks)} 部分）：\n\n{chunk}"
            messages = [
                SystemMessage(content=SYSTEM_PROMPT), 
                HumanMessage(content=prompt)
            ]
            
            try:
                result = await structured_llm_call(self.llm, messages, ClauseExtractResult)
                all_clauses.extend([c.model_dump() for c in result.clauses])
                if i == 0:
                    contract_type = result.contract_type
                print(f"   ✅ 第 {i+1} 块提取了 {len(result.clauses)} 条条款")
            except Exception as e:
                print(f"   ❌ 第 {i+1} 块大模型提取失败: {e}")
        
        print(f"   ✅ 条款提取全部完成！总共成功提取了 {len(all_clauses)} 条条款！类型：{contract_type}")
        return {"clauses": all_clauses, "progress": 0.25}

        
        
        
