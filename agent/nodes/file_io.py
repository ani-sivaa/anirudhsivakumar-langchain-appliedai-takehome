from pathlib import Path
from typing import Dict

from agent.state import AgentState


WORKSPACE_ROOT = Path.cwd()


def validate_path(path: str) -> tuple[bool, str]:
    try:
        file_path = Path(path).resolve()
        file_path.relative_to(WORKSPACE_ROOT)
        return True, ""
    except ValueError:
        return False, f"Access denied: {path} is outside workspace"
    except Exception as e:
        return False, f"Invalid path: {str(e)}"


def read_file(state: AgentState) -> Dict:
    path = state.get("path", "")
    
    if not path:
        return {"error": "No file path specified"}
    
    is_valid, error_msg = validate_path(path)
    if not is_valid:
        return {"error": error_msg}
    
    try:
        file_path = Path(path).resolve()
        
        if not file_path.exists():
            return {"error": f"File not found: {path}"}
        
        if not file_path.is_file():
            return {"error": f"Not a file: {path}"}
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return {"content": content, "error": ""}
        
    except Exception as e:
        return {"error": f"Error reading file {path}: {str(e)}"}


def write_file(state: AgentState) -> Dict:
    path = state.get("path", "")
    content = state.get("modified_content", "")
    
    if not path:
        return {"error": "No file path specified"}
    
    is_valid, error_msg = validate_path(path)
    if not is_valid:
        return {"error": error_msg}
    
    try:
        file_path = Path(path).resolve()
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return {
            "error": "",
            "response": f"Successfully wrote to {path}",
            "messages": [{"role": "assistant", "content": f"Successfully wrote to {path}"}]
        }
        
    except Exception as e:
        return {"error": f"Error writing file {path}: {str(e)}"}


def read_file_multi(state: AgentState) -> Dict:
    path = state.get("path", "")
    
    if not path:
        return {"error": "No file path specified for multi-read"}
    
    is_valid, error_msg = validate_path(path)
    if not is_valid:
        return {"error": error_msg}
    
    try:
        file_path = Path(path).resolve()
        
        if not file_path.exists():
            return {"error": f"File not found: {path}"}
        
        if not file_path.is_file():
            return {"error": f"Not a file: {path}"}
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return {"contents": {path: content}, "error": ""}
        
    except Exception as e:
        return {"error": f"Error reading file {path}: {str(e)}"}


def write_file_multi(state: AgentState) -> Dict:
    path = state.get("path", "")
    modifications = state.get("modifications", {})
    
    if not path:
        return {"error": "No file path specified for multi-write"}
    
    is_valid, error_msg = validate_path(path)
    if not is_valid:
        return {
            "edit_results": [f"✗ {path}: {error_msg}"],
            "error": error_msg
        }
    
    if path not in modifications:
        return {"error": f"No modified content found for {path}"}
    
    content = modifications[path]
    
    try:
        file_path = Path(path).resolve()
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return {
            "edit_results": [f"✓ {path}"],
            "error": ""
        }
        
    except Exception as e:
        return {
            "edit_results": [f"✗ {path}: {str(e)}"],
            "error": f"Error writing file {path}: {str(e)}"
        }
