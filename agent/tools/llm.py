import os
import time
import asyncio
from typing import Optional, Any

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()


def retry_with_backoff(func, max_retries=3, initial_delay=1.0):
    """
    Retries a function if it fails, with exponential backoff.
    Waits 1s, then 2s, then 4s between retries.
    Helpful for when OpenAI API has hiccups or rate limits.
    """
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = initial_delay * (2 ** attempt)
            time.sleep(delay)


async def retry_with_backoff_async(func, max_retries=3, initial_delay=1.0):
    """
    Async version of retry_with_backoff for async functions.
    """
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = initial_delay * (2 ** attempt)
            await asyncio.sleep(delay)


class LLMWrapper:
    def __init__(self, model: Optional[str] = None, temperature: float = 0.0, **kwargs: Any):
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        self.temperature = temperature
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        self.llm = ChatOpenAI(
            model=self.model,
            temperature=temperature,
            api_key=api_key,
            **kwargs
        )
    
    def invoke(self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any) -> str:
        messages = []
        
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        
        messages.append(HumanMessage(content=prompt))
        
        def _invoke():
            response = self.llm.invoke(messages, **kwargs)
            return response.content
        
        return retry_with_backoff(_invoke, max_retries=3, initial_delay=1.0)
    
    async def ainvoke(self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any) -> str:
        """
        Async version of invoke for parallel execution.
        """
        messages = []
        
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        
        messages.append(HumanMessage(content=prompt))
        
        async def _ainvoke():
            response = await self.llm.ainvoke(messages, **kwargs)
            return response.content
        
        return await retry_with_backoff_async(_ainvoke, max_retries=3, initial_delay=1.0)


_default_llm: Optional[LLMWrapper] = None


def get_llm(model: Optional[str] = None, temperature: float = 0.0) -> LLMWrapper:
    global _default_llm
    
    if _default_llm is None:
        _default_llm = LLMWrapper(model=model, temperature=temperature)
    
    return _default_llm
