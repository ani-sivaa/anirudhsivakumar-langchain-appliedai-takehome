from pathlib import Path
from typing import Dict

from agent.state import AgentState
from agent.tools.path.resolver import resolve_path


# Find workspace root by going up from agent code location
# This file is at: project/agent/nodes/file_ops/read.py
# So workspace root is: project/agent/nodes/file_ops/../../../../../ = workspace root
# Use resolve() to get absolute path, then go up 5 levels
# Path breakdown: read.py -> file_ops/ -> nodes/ -> agent/ -> project/ -> workspace_root
_THIS_FILE = Path(__file__).resolve()
WORKSPACE_ROOT = _THIS_FILE.parent.parent.parent.parent.parent  # Go up 5 levels to get workspace root
PROJECT_FOLDER = WORKSPACE_ROOT / "project"
AGENT_GENERATED_CODE_FOLDER = WORKSPACE_ROOT / "agent-generated-code"


def validate_path(path: str) -> tuple[bool, str]:
    """
    Validates file paths to ensure they are within the agent-generated-code folder.
    Blocks edits outside of agent-generated-code and within the project folder.
    """
    try:
        # Resolve path relative to WORKSPACE_ROOT, not current working directory
        # This prevents relative paths from being resolved incorrectly when CWD is project/
        if Path(path).is_absolute():
            file_path = Path(path)
        else:
            file_path = WORKSPACE_ROOT / path
        file_path = file_path.resolve()

        # Check if path is within workspace
        try:
            file_path.relative_to(WORKSPACE_ROOT)
        except ValueError:
            return False, f"Access denied: {path} is outside workspace"

        # Block edits within the project folder
        try:
            file_path.relative_to(PROJECT_FOLDER)
            return False, f"Access denied: {path} is within the project folder. The agent cannot modify its own code."
        except ValueError:
            # Path is not within project folder, which is good
            pass

        # Only allow edits within agent-generated-code folder
        try:
            file_path.relative_to(AGENT_GENERATED_CODE_FOLDER)
            # Path is within agent-generated-code folder, which is allowed
        except ValueError:
            return False, f"Access denied: {path} must be within the agent-generated-code folder. All file operations are restricted to agent-generated-code/"

        return True, ""
    except Exception as e:
        return False, f"Invalid path: {str(e)}"


def read_file(state: AgentState) -> Dict:
    """
    Reads a file and puts the content into state.
    Used in the single-file edit flow.

    Includes fuzzy path matching to handle typos automatically.
    All files are automatically read from agent-generated-code/ folder.
    """
    path = state.get("path", "")

    if not path:
        return {"error": "No file path specified"}

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
    
    # Try to resolve typos in the normalized path
    resolved_path, suggestion = resolve_path(final_path, auto_correct=True)

    # If path was corrected, use the corrected version
    if suggestion:
        # Update state with corrected path so downstream nodes use it
        state["path"] = resolved_path
        path = resolved_path
    else:
        path = final_path

    is_valid, error_msg = validate_path(path)
    if not is_valid:
        return {"error": error_msg}

    try:
        # Convert relative path to absolute for file operations
        if Path(path).is_absolute():
            file_path = Path(path)
        else:
            file_path = WORKSPACE_ROOT / path
        
        file_path = file_path.resolve()

        if not file_path.exists():
            # File doesn't exist - this is OK for new file creation
            # Return empty content so modify_code can create the file
            return {"content": "", "error": ""}

        if not file_path.is_file():
            # Path exists but it's a directory, not a file
            rel_path = path if not Path(path).is_absolute() else str(Path(path).relative_to(WORKSPACE_ROOT))
            return {"error": f"Not a file: {rel_path}"}

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        result = {"content": content, "error": ""}

        # If we auto-corrected a typo, add a note to the response
        if suggestion:
            result["response"] = suggestion

        return result

    except Exception as e:
        return {"error": f"Error reading file {path}: {str(e)}"}

