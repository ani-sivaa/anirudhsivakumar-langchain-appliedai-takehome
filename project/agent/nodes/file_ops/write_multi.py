from pathlib import Path
from typing import Dict
from datetime import datetime

from agent.state import AgentState
from agent.nodes.file_ops.read import validate_path, AGENT_GENERATED_CODE_FOLDER, WORKSPACE_ROOT


def write_file_multi(state: AgentState) -> Dict:
    """
    Writes one file when editing multiple files in parallel.
    Each instance writes its file and adds a result like "SUCCESS: file.py" to the list.
    All files are automatically placed in agent-generated-code/ folder.
    """
    path = state.get("path", "")
    modifications = state.get("modifications", {})
    
    if not path:
        return {"edit_results": [f"FAIL: Unknown - No path"]}

    # Normalize path to ensure it goes to agent-generated-code/
    # Remove any leading slashes or dots, but preserve folder structure
    normalized_path = path.lstrip('/').lstrip('./')
    
    # If path is absolute, try to extract relative part
    if Path(path).is_absolute():
        try:
            normalized_path = str(Path(path).relative_to(WORKSPACE_ROOT))
        except ValueError:
            normalized_path = Path(path).name
    
    # Remove agent-generated-code prefix if already present (avoid duplication)
    if normalized_path.startswith("agent-generated-code/"):
        normalized_path = normalized_path[len("agent-generated-code/"):]
    
    # Always prepend agent-generated-code to ensure files go there
    final_path = f"agent-generated-code/{normalized_path}"
    
    # Now validate the normalized path
    is_valid, error_msg = validate_path(final_path)
    if not is_valid:
        return {"edit_results": [f"FAIL: {path} - {error_msg}"]}
    
    # Use the normalized path
    path = final_path

    if not modifications:
        return {"edit_results": [f"FAIL: {path} - modifications is empty/None"]}

    if path not in modifications:
        return {"edit_results": [f"FAIL: {path} - Path not in modifications"]}

    content = modifications[path]

    # If content is an error message from previous stages, don't write it
    if isinstance(content, str) and content.startswith("ERROR:"):
        return {"edit_results": [f"FAIL: {path} - {content}"]}

    # Timing for parallel execution visibility
    start_time = datetime.now()
    short_path = Path(path).name if path else ""

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

        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"  [PARALLEL] Wrote: {short_path} ({elapsed:.3f}s)", flush=True)

        # Use relative path for cleaner output
        rel_path = path if not Path(path).is_absolute() else str(Path(path).relative_to(WORKSPACE_ROOT))
        return {"edit_results": [f"SUCCESS: {rel_path}"]}

    except Exception as e:
        return {"edit_results": [f"FAIL: {path} - {str(e)}"]}

