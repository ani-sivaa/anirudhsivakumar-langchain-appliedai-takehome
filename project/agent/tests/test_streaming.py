import pytest
import asyncio
from agent.graph import get_agent_graph


@pytest.mark.asyncio
async def test_streaming_basic():
    """Test that streaming mode works and yields updates."""
    agent_graph = await get_agent_graph()
    config = {"configurable": {"thread_id": "test-stream-001"}}
    
    events = []
    async for event in agent_graph.astream(
        {"user_input": "hello"},
        config=config,
        stream_mode="updates"
    ):
        events.append(event)
    
    assert len(events) > 0
    
    node_names = []
    for event in events:
        node_names.extend(event.keys())
    
    assert "determine_intent" in node_names


@pytest.mark.asyncio
async def test_streaming_with_state_inspection():
    """Test that streaming maintains conversation context."""
    agent_graph = await get_agent_graph()
    config = {"configurable": {"thread_id": "test-stream-002"}}
    
    async for _ in agent_graph.astream(
        {"user_input": "What's 2+2?"},
        config=config,
        stream_mode="updates"
    ):
        pass
    
    state = await agent_graph.aget_state(config)
    
    assert state.values.get("action") is not None
    assert state.config["configurable"]["thread_id"] == "test-stream-002"


@pytest.mark.asyncio
async def test_streaming_maintains_context():
    """Test that streaming maintains conversation context."""
    agent_graph = await get_agent_graph()
    thread_id = "test-stream-context-001"
    config = {"configurable": {"thread_id": thread_id}}
    
    async for _ in agent_graph.astream(
        {"user_input": "My name is Alice"},
        config=config,
        stream_mode="updates"
    ):
        pass
    
    async for _ in agent_graph.astream(
        {"user_input": "What did I just tell you?"},
        config=config,
        stream_mode="updates"
    ):
        pass
    
    state = await agent_graph.aget_state(config)
    messages = state.values.get("messages", [])
    
    assert len(messages) >= 2
