import pytest
import asyncio
from agent.tools.memory.interface import get_memory_store, save_memory, get_memory, search_memories
from agent.nodes.memory.user_memory import save_user_memory, recall_user_memory
from agent.graph import get_agent_graph


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


@pytest.mark.asyncio
async def test_save_user_memory_node():
    state = {
        "user_id": "test_user",
        "memory_key": "preference",
        "memory_value": {"language": "python"}
    }
    
    result = await save_user_memory(state)
    assert "Saved memory" in result["response"]
    assert result["error"] == ""


@pytest.mark.asyncio
async def test_recall_user_memory_node():
    namespace = ("users", "test_user_recall")
    save_memory(namespace, "skill", {"skill": "LangGraph"})
    
    state = {
        "user_id": "test_user_recall",
        "memory_key": "skill"
    }
    
    result = await recall_user_memory(state)
    assert "LangGraph" in result["response"]


@pytest.mark.asyncio
async def test_recall_missing_memory():
    state = {
        "user_id": "test_user_missing",
        "memory_key": "nothing"
    }
    
    result = await recall_user_memory(state)
    assert "don't have any memory" in result["response"].lower() or "no memory" in result["response"].lower()


@pytest.mark.asyncio
async def test_agent_remember_intent():
    agent_graph = await get_agent_graph()
    config = {"configurable": {"thread_id": "test_remember"}}
    
    result = await agent_graph.ainvoke(
        {"user_input": "remember my favorite color is blue"},
        config=config
    )
    
    assert result["action"] == "remember"
    assert "memory_key" in result


@pytest.mark.asyncio
async def test_agent_recall_intent():
    agent_graph = await get_agent_graph()
    namespace = ("users", "default_user")
    save_memory(namespace, "city", {"city": "San Francisco"})
    
    config = {"configurable": {"thread_id": "test_recall"}}
    
    result = await agent_graph.ainvoke(
        {"user_input": "what city did I tell you about?"},
        config=config
    )
    
    assert result["action"] == "recall"

