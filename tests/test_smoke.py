import pytest
from agent.nodes.shell import run_shell
from agent.graph import agent_graph


def test_shell_basic_command():
    state = {"command": "echo hello"}
    result = run_shell(state)
    
    assert result["return_code"] == 0
    assert "hello" in result["shell_output"]
    assert result["error"] == ""


def test_shell_command_with_exit_code():
    state = {"command": "exit 1"}
    result = run_shell(state)
    
    assert result["return_code"] == 1


def test_shell_no_command():
    state = {}
    result = run_shell(state)
    
    assert "error" in result
    assert "No command provided" in result["error"]


def test_shell_list_files():
    state = {"command": "ls"}
    result = run_shell(state)
    
    assert result["return_code"] == 0
    assert result["shell_output"] is not None


def test_agent_shell_intent():
    config = {"configurable": {"thread_id": "test_shell"}}
    
    result = agent_graph.invoke(
        {"user_input": "run echo test123"},
        config=config
    )
    
    assert result["action"] == "shell"
    assert "test123" in result["shell_output"]
