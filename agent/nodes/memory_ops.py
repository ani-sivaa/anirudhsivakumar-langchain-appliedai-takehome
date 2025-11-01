from typing import Dict
from agent.state import AgentState
from agent.tools.memory import save_memory, get_memory, search_memories


def save_user_memory(state: AgentState) -> Dict:
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


def recall_user_memory(state: AgentState) -> Dict:
    memory_key = state.get("memory_key", "")
    user_id = state.get("user_id", "default_user")
    
    if not memory_key:
        return {"error": "No memory key provided"}
    
    namespace = ("users", user_id)
    memory = get_memory(namespace, memory_key)
    
    if memory:
        content = f"Found memory '{memory_key}': {memory}"
    else:
        content = f"No memory found for '{memory_key}'"
    
    return {
        "response": content,
        "messages": [{"role": "assistant", "content": content}],
        "error": ""
    }


def search_user_memories(state: AgentState) -> Dict:
    query = state.get("memory_query", "")
    user_id = state.get("user_id", "default_user")
    
    namespace = ("users", user_id)
    memories = search_memories(namespace, query=query)
    
    if memories:
        content = f"Found {len(memories)} memories:\n" + "\n".join([str(m) for m in memories[:5]])
    else:
        content = "No memories found"
    
    return {
        "response": content,
        "messages": [{"role": "assistant", "content": content}],
        "error": ""
    }

