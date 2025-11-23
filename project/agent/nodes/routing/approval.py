from typing import Dict
from langgraph.types import interrupt

from agent.state import AgentState
from agent.tools.interrupts.safety import is_dangerous_command, is_sensitive_file, format_file_diff


def check_approval_needed(state: AgentState) -> Dict:
    """
    Checks if the operation needs human approval before running.
    Looks for dangerous shell commands (rm -rf, sudo) and sensitive files (.env, secrets).
    """
    action = state.get("action", "")
    
    if action == "shell":
        command = state.get("command", "")
        if is_dangerous_command(command):
            return {
                "approval_required": True,
                "approval_request": {
                    "type": "shell_execution",
                    "question": f"Execute potentially dangerous command?",
                    "command": command,
                    "warning": "This command could be destructive"
                }
            }
    
    elif action == "edit":
        path = state.get("path", "")
        if is_sensitive_file(path):
            content = state.get("content", "")
            modified = state.get("modified_content", "")
            
            if content and modified:
                diff = format_file_diff(content, modified, path)
            else:
                diff = f"New file: {path}"
            
            return {
                "approval_required": True,
                "approval_request": {
                    "type": "file_modification",
                    "question": f"Modify sensitive file: {path}?",
                    "path": path,
                    "diff": diff,
                    "warning": " This is a sensitive file"
                }
            }
    
    return {"approval_required": False}


def request_approval(state: AgentState) -> Dict:
    """
    Pauses execution to ask the user for approval.
    Uses LangGraph's interrupt() to wait for user input.
    
    Note: The interrupt() will cause the graph to pause. When resumed via
    update_state() with approval_response, this node completes and returns
    that response for routing.
    """
    approval_request = state.get("approval_request", {})
    
    if not approval_request:
        return {"approval_response": "approve"}
    
    # Check if we already have a response (from update_state)
    existing_response = state.get("approval_response")
    if existing_response:
        # Already decided, just return it
        return {"approval_response": existing_response}
    
    # Pause and wait for user input
    interrupt(approval_request)
    
    # After resume, get the response that was set via update_state
    return {"approval_response": state.get("approval_response", "deny")}


def route_approval(state: AgentState) -> str:
    """Routes to either the action or approval request based on whether approval is needed."""
    if not state.get("approval_required", False):
        action = state.get("action", "chat")

        if action == "shell":
            return "shell"
        elif action == "edit":
            return "read_file"
        elif action == "edit_multi":
            return "edit_multi"
        elif action == "install":
            return "install"
        elif action == "remember":
            return "remember"
        elif action == "recall":
            return "recall"
        elif action == "project":
            return "project"
        elif action == "project_context":
            return "project_context"
        elif action == "index_codebase":
            return "index_codebase"
        elif action == "ask_codebase":
            return "ask_codebase"

        return "chat"

    return "request_approval"


def route_after_approval(state: AgentState) -> str:
    """Routes based on user's approval decision - either proceed or go to denied node."""
    approval = state.get("approval_response", "deny")

    if approval == "approve":
        action = state.get("action", "chat")

        if action == "shell":
            return "shell"
        elif action == "edit":
            return "read_file"
        elif action == "edit_multi":
            return "edit_multi"
        elif action == "install":
            return "install"
        elif action == "remember":
            return "remember"
        elif action == "recall":
            return "recall"
        elif action == "project":
            return "project"
        elif action == "project_context":
            return "project_context"
        elif action == "index_codebase":
            return "index_codebase"
        elif action == "ask_codebase":
            return "ask_codebase"

        return "chat"

    return "denied"


def handle_denial(state: AgentState) -> Dict:
    """Handles when user denies approval - just returns an error message."""
    action = state.get("action", "")
    
    return {
        "response": f"Operation denied by user: {action}",
        "messages": [{"role": "assistant", "content": f"Operation '{action}' was denied by user"}],
        "error": "Operation denied by user"
    }

