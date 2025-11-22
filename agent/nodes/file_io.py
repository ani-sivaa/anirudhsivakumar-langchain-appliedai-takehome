from pathlib import Path
from typing import Dict
from datetime import datetime

from agent.state import AgentState
from agent.tools.path_resolver import resolve_path


WORKSPACE_ROOT = Path.cwd()


def validate_path(path: str) -> tuple[bool, str]:
    """
    Makes sure the file path isn't trying to escape the workspace.
    Blocks things like ../../etc/passwd or symlinks pointing outside.
    """
    try:
        file_path = Path(path).resolve()
        file_path.relative_to(WORKSPACE_ROOT)
        return True, ""
    except ValueError:
        return False, f"Access denied: {path} is outside workspace"
    except Exception as e:
        return False, f"Invalid path: {str(e)}"


def read_file(state: AgentState) -> Dict:
    """
    Reads a file and puts the content into state.
    Used in the single-file edit flow.

    Includes fuzzy path matching to handle typos automatically.
    """
    path = state.get("path", "")

    if not path:
        return {"error": "No file path specified"}

    # Try to resolve typos in the path
    resolved_path, suggestion = resolve_path(path, auto_correct=True)

    # If path was corrected, use the corrected version
    if suggestion:
        # Update state with corrected path so downstream nodes use it
        state["path"] = resolved_path
        path = resolved_path

    is_valid, error_msg = validate_path(path)
    if not is_valid:
        return {"error": error_msg}

    try:
        file_path = Path(path).resolve()

        if not file_path.exists():
            # If still not found after correction, give helpful error
            error = f"File not found: {path}"
            if suggestion:
                error += f"\n{suggestion}"
            return {"error": error}

        if not file_path.is_file():
            return {"error": f"Not a file: {path}"}

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        result = {"content": content, "error": ""}

        # If we auto-corrected a typo, add a note to the response
        if suggestion:
            result["response"] = suggestion

        return result

    except Exception as e:
        return {"error": f"Error reading file {path}: {str(e)}"}


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
        file_path = Path(path).resolve()
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        user_input = state.get("user_input", "")
        response_msg = f"Successfully wrote to {path}"
        
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
        file_path = Path(path).resolve()
        
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


def write_file_multi(state: AgentState) -> Dict:
    """
    Writes one file when editing multiple files in parallel.
    Each instance writes its file and adds a result like "SUCCESS: file.py" to the list.
    """
    path = state.get("path", "")
    modifications = state.get("modifications", {})
    
    if not path:
        return {"edit_results": [f"FAIL: Unknown - No path"]}

    is_valid, error_msg = validate_path(path)
    if not is_valid:
        return {"edit_results": [f"FAIL: {path} - {error_msg}"]}

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
        file_path = Path(path).resolve()
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"  [PARALLEL] Wrote: {short_path} ({elapsed:.3f}s)", flush=True)

        # Use relative path for cleaner output
        try:
            rel_path = Path(path).relative_to(Path.cwd())
            return {"edit_results": [f"SUCCESS: {rel_path}"]}
        except ValueError:
            # If relative path fails, use just the filename
            return {"edit_results": [f"SUCCESS: {Path(path).name}"]}

    except Exception as e:
        return {"edit_results": [f"FAIL: {path} - {str(e)}"]}

