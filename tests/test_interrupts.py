import pytest
from agent.tools.interrupts import is_dangerous_command, is_sensitive_file, format_file_diff
from agent.nodes.approval import check_approval_needed, handle_denial


def test_dangerous_command_detection():
    assert is_dangerous_command("rm -rf /") == True
    assert is_dangerous_command("sudo apt install") == True
    assert is_dangerous_command("git push --force") == True
    assert is_dangerous_command("ls -la") == False
    assert is_dangerous_command("echo hello") == False


def test_sensitive_file_detection():
    assert is_sensitive_file(".env") == True
    assert is_sensitive_file("config/.env.local") == True
    assert is_sensitive_file("requirements.txt") == True
    assert is_sensitive_file("package.json") == True
    assert is_sensitive_file("main.py") == False
    assert is_sensitive_file("README.md") == False


def test_file_diff_format():
    original = "line 1\nline 2\nline 3"
    modified = "line 1\nline 2 modified\nline 3"
    
    diff = format_file_diff(original, modified, "test.py")
    
    assert "test.py" in diff
    assert "line 2" in diff


def test_check_approval_dangerous_shell():
    state = {
        "action": "shell",
        "command": "rm -rf /"
    }
    
    result = check_approval_needed(state)
    
    assert result["approval_required"] == True
    assert result["approval_request"]["type"] == "shell_execution"


def test_check_approval_safe_shell():
    state = {
        "action": "shell",
        "command": "ls -la"
    }
    
    result = check_approval_needed(state)
    
    assert result.get("approval_required", False) == False


def test_check_approval_sensitive_file():
    state = {
        "action": "edit",
        "path": ".env",
        "content": "OLD=value",
        "modified_content": "NEW=value"
    }
    
    result = check_approval_needed(state)
    
    assert result["approval_required"] == True
    assert result["approval_request"]["type"] == "file_modification"


def test_check_approval_normal_file():
    state = {
        "action": "edit",
        "path": "test.py"
    }
    
    result = check_approval_needed(state)
    
    assert result.get("approval_required", False) == False


def test_handle_denial():
    state = {"action": "shell"}
    
    result = handle_denial(state)
    
    assert "denied" in result["response"]
    assert result["error"] == "Operation denied by user"

