from pathlib import Path
from typing import Dict

from agent.state import AgentState
from agent.tools.path.resolver import resolve_path


WORKSPACE_ROOT = Path.cwd()
PROJECT_FOLDER = WORKSPACE_ROOT / "project"
AGENT_GENERATED_CODE_FOLDER = WORKSPACE_ROOT / "agent-generated-code"


def validate_path(path: str) -> tuple[bool, str]:
    """
    Validates file paths to ensure they are within the agent-generated-code folder.
    Blocks edits outside of agent-generated-code and within the project folder.
    """
    try:
        file_path = Path(path).resolve()
        
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
        # Convert relative path to absolute for file operations
        if Path(path).is_absolute():
            file_path = Path(path)
        else:
            file_path = WORKSPACE_ROOT / path
        
        file_path = file_path.resolve()

        if not file_path.exists():
            # If still not found after correction, give helpful error
            rel_path = path if not Path(path).is_absolute() else str(Path(path).relative_to(WORKSPACE_ROOT))
            error = f"File not found: {rel_path}"
            if suggestion:
                error += f"\n{suggestion}"
            return {"error": error}

        if not file_path.is_file():
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

