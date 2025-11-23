from pathlib import Path
from typing import Dict
from datetime import datetime

from agent.state import AgentState
from agent.nodes.file_ops.read import validate_path, WORKSPACE_ROOT


def read_file_multi(state: AgentState) -> Dict:
    """
    Reads one file when editing multiple files in parallel.
    Gets spawned multiple times by Send() - each instance reads its own file.
    """
    path = state.get("path", "")
    
    if not path:
        # Don't write to 'error' field from parallel nodes - causes conflicts
        # Instead, write empty content which will be caught later
        return {"contents": {}}
    
    # Timing for parallel execution visibility
    start_time = datetime.now()
    short_path = Path(path).name if path else ""
    
    is_valid, error_msg = validate_path(path)
    if not is_valid:
        # Write to contents with error message as value
        return {"contents": {path: f"ERROR: {error_msg}"}}
    
    try:
        # Convert relative path to absolute for file operations
        if Path(path).is_absolute():
            file_path = Path(path)
        else:
            file_path = WORKSPACE_ROOT / path
        
        file_path = file_path.resolve()
        
        if not file_path.exists():
            return {"contents": {path: f"ERROR: File not found"}}
        
        if not file_path.is_file():
            return {"contents": {path: f"ERROR: Not a file"}}
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"  [PARALLEL] Read: {short_path} ({elapsed:.3f}s)", flush=True)
        
        return {"contents": {path: content}}
        
    except Exception as e:
        return {"contents": {path: f"ERROR: {str(e)}"}}

