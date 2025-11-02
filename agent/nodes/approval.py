from typing import Dict
from langgraph.types import interrupt

from agent.state import AgentState
from agent.tools.interrupts import is_dangerous_command, is_sensitive_file, format_file_diff


def check_approval_needed(state: AgentState) -> Dict:
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
                    "warning": "⚠️ This command could be destructive"
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
                    "warning": "⚠️ This is a sensitive file"
                }
            }
    
    return {"approval_required": False}


def request_approval(state: AgentState) -> Dict:
    approval_request = state.get("approval_request", {})
    
    if not approval_request:
        return {"approval_response": "approve"}
    
    approval = interrupt(approval_request)
    
    return {"approval_response": approval}


def route_approval(state: AgentState) -> str:
    if not state.get("approval_required", False):
        action = state.get("action", "chat")
        
        if action == "shell":
            return "shell"
        elif action == "edit":
            return "read_file"
        elif action == "review":
            return "review"
        elif action == "remember":
            return "remember"
        elif action == "recall":
            return "recall"
        elif action == "project":
            return "project"
        
        return "chat"
    
    return "request_approval"


def route_after_approval(state: AgentState) -> str:
    approval = state.get("approval_response", "deny")
    
    if approval == "approve":
        action = state.get("action", "chat")
        
        if action == "shell":
            return "shell"
        elif action == "edit":
            return "read_file"
        elif action == "review":
            return "review"
        elif action == "remember":
            return "remember"
        elif action == "recall":
            return "recall"
        elif action == "project":
            return "project"
        
        return "chat"
    
    return "denied"


def handle_denial(state: AgentState) -> Dict:
    action = state.get("action", "")
    
    return {
        "response": f"Operation denied by user: {action}",
        "messages": [{"role": "assistant", "content": f"Operation '{action}' was denied by user"}],
        "error": "Operation denied by user"
    }

