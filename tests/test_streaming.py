import pytest
from agent.graph import agent_graph


def test_streaming_basic():
    """Test that streaming mode works and yields updates."""
    config = {"configurable": {"thread_id": "test-stream-001"}}
    
    events = list(agent_graph.stream(
        {"user_input": "hello"},
        config=config,
        stream_mode="updates"
    ))
    
    assert len(events) > 0
    
    node_names = []
    for event in events:
        node_names.extend(event.keys())
    
    assert "determine_intent" in node_names


def test_streaming_with_state_inspection():
    """Test that we can inspect state after streaming."""
    config = {"configurable": {"thread_id": "test-stream-002"}}
    
    for _ in agent_graph.stream(
        {"user_input": "What's 2+2?"},
        config=config,
        stream_mode="updates"
    ):
        pass
    
    state = agent_graph.get_state(config)
    
    assert state.values.get("action") is not None
    assert state.config["configurable"]["thread_id"] == "test-stream-002"


def test_streaming_maintains_context():
    """Test that streaming maintains conversation context."""
    thread_id = "test-stream-context-001"
    config = {"configurable": {"thread_id": thread_id}}
    
    list(agent_graph.stream(
        {"user_input": "My name is Alice"},
        config=config,
        stream_mode="updates"
    ))
    
    list(agent_graph.stream(
        {"user_input": "What did I just tell you?"},
        config=config,
        stream_mode="updates"
    ))
    
    state = agent_graph.get_state(config)
    messages = state.values.get("messages", [])
    
    assert len(messages) >= 2

