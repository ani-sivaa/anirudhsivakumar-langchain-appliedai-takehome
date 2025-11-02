import pytest
import os
import shutil
from agent.nodes.project import plan_project, create_project_file, summarize_project


def test_plan_project():
    state = {"project_instruction": "create 3 python files for a calculator"}
    result = plan_project(state)
    
    assert "project_files" in result
    assert len(result["project_files"]) > 0
    assert result["error"] == ""


def test_create_project_file():
    state = {
        "file_path": "test_output/test.txt",
        "file_description": "a simple hello world file"
    }
    
    result = create_project_file(state)
    
    assert "messages" in result
    assert len(result["messages"]) > 0
    assert "test_output/test.txt" in result["messages"][0]["content"]
    assert os.path.exists("test_output/test.txt")
    
    # Cleanup
    shutil.rmtree("test_output", ignore_errors=True)


def test_summarize_project():
    state = {
        "project_files": [
            {"path": "file1.py", "description": "test"},
            {"path": "file2.py", "description": "test"}
        ],
        "messages": [
            {"role": "assistant", "content": "✓ file1.py"},
            {"role": "assistant", "content": "✓ file2.py"}
        ]
    }
    
    result = summarize_project(state)
    
    assert "Project complete" in result["response"]
    assert "2 files" in result["response"]

