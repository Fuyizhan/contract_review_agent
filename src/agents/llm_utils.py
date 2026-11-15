# src/agents/llm_utils.py
import asyncio
from langchain_openai import ChatOpenAI
from src.config import settings
from pydantic import BaseModel
from typing import Any, List
from langchain_core.messages import BaseMessage
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import openai

def get_llm() -> ChatOpenAI:
    # 设置超时时间为 60 秒
    return ChatOpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
        model=settings.LLM_MODEL,
        temperature=0.0,
        timeout=60.0  # <--- 【新增】超时控制
    )

# 【新增】使用 tenacity 实现指数退避重试
# stop_after_attempt(3): 最多试 3 次
# wait_exponential(multiplier=1, min=2, max=10): 等 2s, 4s, 8s...
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((openai.APIError, openai.APIConnectionError, asyncio.TimeoutError)),
    reraise=True
)
async def _call_llm_with_retry(structured_llm, messages):
    """带重试机制的大模型调用"""
    return await structured_llm.ainvoke(messages)

async def structured_llm_call(llm: ChatOpenAI, messages: List[BaseMessage], schema: type[BaseModel]) -> Any:
    """调用大模型，并强制它按指定的 Pydantic schema 输出结构化数据。"""
    # 依然使用 json_mode 兼容 DeepSeek
    structured_llm = llm.with_structured_output(schema, method="json_mode")
    
    # 调用带有重试机制的封装函数
    return await _call_llm_with_retry(structured_llm, messages)