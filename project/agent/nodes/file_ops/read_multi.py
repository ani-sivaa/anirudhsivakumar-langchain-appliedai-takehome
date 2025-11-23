import os
from pathlib import Path
from typing import Dict
from datetime import datetime

from agent.state import AgentState
from agent.nodes.file_ops.read import validate_path, WORKSPACE_ROOT, AGENT_GENERATED_CODE_FOLDER


def read_file_multi(state: AgentState) -> Dict:
    """
    Reads one file when editing multiple files in parallel.
    Gets spawned multiple times by Send() - each instance reads its own file.
    All files are automatically read from agent-generated-code/ folder.
    """
    path = state.get("path", "")
    
    if not path:
        # Don't write to 'error' field from parallel nodes - causes conflicts
        # Instead, write empty content which will be caught later
        return {"contents": {}}
    
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
    
    # Always prepend agent-generated-code to ensure files are read from there
    final_path = f"agent-generated-code/{normalized_path}"
    
    # Timing for parallel execution visibility
    start_time = datetime.now()
    short_path = Path(final_path).name if final_path else ""
    
    is_valid, error_msg = validate_path(final_path)
    if not is_valid:
        # Write to contents with error message as value
        return {"contents": {path: f"ERROR: {error_msg}"}}
    
    # Use the normalized path
    path = final_path
    
    try:
        # Convert relative path to absolute for file operations
        if Path(path).is_absolute():
            file_path = Path(path)
        else:
            file_path = WORKSPACE_ROOT / path
        
        file_path = file_path.resolve()
        
        if not file_path.exists():
            # If file not found, try searching for it by name in subdirectories
            # This handles cases where intent router only extracted filename (e.g., "a.py" instead of "test/a.py")
            filename = Path(normalized_path).name
            if filename != normalized_path:
                # Already tried with folder structure, no need to search
                return {"contents": {path: f"ERROR: File not found"}}
            
            # Search for file by name in agent-generated-code folder
            found_path = None
            if AGENT_GENERATED_CODE_FOLDER.exists():
                for root, dirs, files in os.walk(AGENT_GENERATED_CODE_FOLDER):
                    # Skip hidden directories
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    if filename in files:
                        found_path = Path(root) / filename
                        # Get relative path from workspace root
                        try:
                            rel_path = found_path.relative_to(WORKSPACE_ROOT)
                            found_path = str(rel_path)
                        except ValueError:
                            found_path = str(found_path)
                        break
            
            if found_path:
                # Update path to the found file
                path = found_path
                file_path = WORKSPACE_ROOT / found_path if not Path(found_path).is_absolute() else Path(found_path)
                file_path = file_path.resolve()
            else:
                return {"contents": {path: f"ERROR: File not found: {filename}"}}
        
        if not file_path.is_file():
            return {"contents": {path: f"ERROR: Not a file"}}
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"  [PARALLEL] Read: {short_path} ({elapsed:.3f}s)", flush=True)
        
        return {"contents": {path: content}}
        
    except Exception as e:
        return {"contents": {path: f"ERROR: {str(e)}"}}

