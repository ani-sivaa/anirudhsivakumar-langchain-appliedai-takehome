from pathlib import Path
from typing import Dict

from agent.state import AgentState


def read_file(state: AgentState) -> Dict:
    path = state.get("path", "")
    
    if not path:
        return {"error": "No file path specified"}
    
    try:
        file_path = Path(path)
        
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
    
    try:
        file_path = Path(path)
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
