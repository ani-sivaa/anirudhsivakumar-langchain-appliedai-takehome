from pathlib import Path
from typing import Dict

from agent.state import AgentState
from agent.nodes.file_ops.read import validate_path, AGENT_GENERATED_CODE_FOLDER, WORKSPACE_ROOT


def write_file(state: AgentState) -> Dict:
    """
    Writes the modified content to disk.
    Creates folders if they don't exist.
    """
    path = state.get("path", "")
    content = state.get("modified_content", "")
    
    if not path:
        return {"error": "No file path specified"}
    
    is_valid, error_msg = validate_path(path)
    if not is_valid:
        return {"error": error_msg}
    
    try:
        # Ensure agent-generated-code folder exists
        AGENT_GENERATED_CODE_FOLDER.mkdir(parents=True, exist_ok=True)
        
        # Convert relative path to absolute for file operations
        if Path(path).is_absolute():
            file_path = Path(path)
        else:
            file_path = WORKSPACE_ROOT / path
        
        file_path = file_path.resolve()
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        user_input = state.get("user_input", "")
        # Use relative path in response message
        rel_path = str(Path(path).relative_to(WORKSPACE_ROOT)) if Path(path).is_absolute() else path
        response_msg = f"Successfully wrote to {rel_path}"
        
        return {
            "error": "",
            "response": response_msg,
            "messages": [
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": response_msg}
            ]
        }
        
    except Exception as e:
        return {"error": f"Error writing file {path}: {str(e)}"}

