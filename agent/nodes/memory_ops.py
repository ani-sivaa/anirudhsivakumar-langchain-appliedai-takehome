from typing import Dict
from agent.state import AgentState
from agent.tools.memory import save_memory, get_memory
from agent.tools.llm import get_llm


def save_user_memory(state: AgentState) -> Dict:
    """
    Saves stuff to long-term memory (SQLite database).
    Like when user says "remember my name is John".
    """
    memory_key = state.get("memory_key", "")
    memory_value = state.get("memory_value", {})
    user_id = state.get("user_id", "default_user")
    
    if not memory_key:
        return {"error": "No memory key provided"}
    
    namespace = ("users", user_id)
    result = save_memory(namespace, memory_key, memory_value)
    
    return {
        "response": result,
        "messages": [{"role": "assistant", "content": result}],
        "error": ""
    }


async def recall_user_memory(state: AgentState) -> Dict:
    """
    Retrieves stuff from long-term memory and formats it naturally with LLM.
    Like when user asks "what's my name?" and we saved it earlier.
    """
    memory_key = state.get("memory_key", "")
    user_id = state.get("user_id", "default_user")
    user_input = state.get("user_input", "")

    if not memory_key:
        return {"error": "No memory key provided"}

    namespace = ("users", user_id)
    memory = get_memory(namespace, memory_key)

    if not memory:
        content = f"I don't have any memory saved for '{memory_key}'"
        return {
            "response": content,
            "messages": [{"role": "assistant", "content": content}],
            "error": ""
        }

    try:
        llm = get_llm(temperature=0.7)

        system_prompt = """You are Jarvis, a helpful coding assistant. Generate a natural, conversational response based on the retrieved memory.

Be friendly and concise. Answer the user's question naturally without just dumping the raw data."""

        user_prompt = f"""User asked: {user_input}

Retrieved memory: {memory}

Generate a natural response:"""

        content = await llm.ainvoke(prompt=user_prompt, system_prompt=system_prompt)

        return {
            "response": content,
            "messages": [{"role": "assistant", "content": content}],
            "error": ""
        }

    except Exception as e:
        fallback = f"I found this: {memory}"
        return {
            "response": fallback,
            "messages": [{"role": "assistant", "content": fallback}],
            "error": ""
        }

