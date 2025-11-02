import os
import shutil
from unittest.mock import patch, MagicMock

from agent.state import AgentState
from agent.nodes.file_io import read_file_multi, write_file_multi
from agent.nodes.modify import modify_code_multi
from agent.nodes.summarize_edit import summarize_multi_edit


def test_read_file_multi():
    test_file = "test_read_multi.txt"
    
    with open(test_file, "w") as f:
        f.write("test content")
    
    try:
        state: AgentState = {"path": test_file}
        result = read_file_multi(state)
        
        assert "contents" in result
        assert test_file in result["contents"]
        assert result["contents"][test_file] == "test content"
        assert result["error"] == ""
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)


def test_modify_code_multi():
    state: AgentState = {
        "path": "utils.py",
        "contents": {"utils.py": "def add(a, b):\n    return a + b"},
        "edit_instruction": "add type hints"
    }
    
    with patch("agent.tools.llm.get_llm") as mock_get_llm:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "def add(a: int, b: int) -> int:\n    return a + b"
        mock_get_llm.return_value = mock_llm
        
        result = modify_code_multi(state)
        
        assert "modifications" in result
        assert "utils.py" in result["modifications"]
        assert "int" in result["modifications"]["utils.py"]
        assert result["error"] == ""


def test_write_file_multi():
    test_dir = "test_multi_write"
    os.makedirs(test_dir, exist_ok=True)
    test_file = os.path.join(test_dir, "output.txt")
    
    try:
        state: AgentState = {
            "path": test_file,
            "modifications": {test_file: "modified content"}
        }
        
        result = write_file_multi(state)
        
        assert "edit_results" in result
        assert len(result["edit_results"]) == 1
        assert result["edit_results"][0].startswith("✓")
        assert os.path.exists(test_file)
        
        with open(test_file, "r") as f:
            content = f.read()
        assert content == "modified content"
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)


def test_summarize_multi_edit():
    state: AgentState = {
        "paths": ["file1.py", "file2.py", "file3.py"],
        "edit_results": ["✓ file1.py", "✓ file2.py", "✗ file3.py: error"]
    }
    
    result = summarize_multi_edit(state)
    
    assert "response" in result
    assert "Edited 3 file(s)" in result["response"]
    assert "✓ file1.py" in result["response"]
    assert "✓ file2.py" in result["response"]
    assert "✗ file3.py" in result["response"]
    assert "2 succeeded, 1 failed" in result["response"]
    assert result["error"] == ""


def test_summarize_multi_edit_all_success():
    state: AgentState = {
        "paths": ["file1.py", "file2.py"],
        "edit_results": ["✓ file1.py", "✓ file2.py"]
    }
    
    result = summarize_multi_edit(state)
    
    assert "response" in result
    assert "Edited 2 file(s)" in result["response"]
    assert "2 succeeded, 0 failed" not in result["response"]

