import pytest
from agent.tools.memory import get_memory_store, save_memory, get_memory, search_memories
from agent.nodes.memory_ops import save_user_memory, recall_user_memory
from agent.graph import agent_graph


def test_memory_store_basics():
    store = get_memory_store()
    
    namespace = ("test", "user1")
    save_memory(namespace, "name", {"name": "Alice"})
    
    result = get_memory(namespace, "name")
    assert result == {"name": "Alice"}


def test_memory_not_found():
    store = get_memory_store()
    namespace = ("test", "user2")
    
    result = get_memory(namespace, "nonexistent")
    assert result is None


def test_save_user_memory_node():
    state = {
        "user_id": "test_user",
        "memory_key": "preference",
        "memory_value": {"language": "python"}
    }
    
    result = save_user_memory(state)
    assert "Saved memory" in result["response"]
    assert result["error"] == ""


def test_recall_user_memory_node():
    namespace = ("users", "test_user_recall")
    save_memory(namespace, "skill", {"skill": "LangGraph"})
    
    state = {
        "user_id": "test_user_recall",
        "memory_key": "skill"
    }
    
    result = recall_user_memory(state)
    assert "LangGraph" in result["response"]


def test_recall_missing_memory():
    state = {
        "user_id": "test_user_missing",
        "memory_key": "nothing"
    }
    
    result = recall_user_memory(state)
    assert "No memory found" in result["response"]


def test_agent_remember_intent():
    config = {"configurable": {"thread_id": "test_remember"}}
    
    result = agent_graph.invoke(
        {"user_input": "remember my favorite color is blue"},
        config=config
    )
    
    assert result["action"] == "remember"
    assert "memory_key" in result


def test_agent_recall_intent():
    namespace = ("users", "default_user")
    save_memory(namespace, "city", {"city": "San Francisco"})
    
    config = {"configurable": {"thread_id": "test_recall"}}
    
    result = agent_graph.invoke(
        {"user_input": "what city did I tell you about?"},
        config=config
    )
    
    assert result["action"] == "recall"

