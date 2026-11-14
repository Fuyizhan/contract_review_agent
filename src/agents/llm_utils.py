# src/agents/llm_utils.py
from langchain_openai import ChatOpenAI
from src.config import settings
from pydantic import BaseModel
from typing import Any, List
from langchain_core.messages import BaseMessage

def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        model=settings.LLM_MODEL,
        temperature=0.0
    )

# 【修改这里】参数改成 messages: List[BaseMessage]
async def structured_llm_call(llm: ChatOpenAI, messages: List[BaseMessage], schema: type[BaseModel]) -> Any:
    """调用大模型，强制按指定的 Pydantic schema 输出。"""
    structured_llm = llm.with_structured_output(schema,method="json_mode")
    return await structured_llm.ainvoke(messages)