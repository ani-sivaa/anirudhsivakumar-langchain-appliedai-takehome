import json
from typing import Dict

from agent.state import AgentState
from agent.tools.llm import get_llm
from agent.tools.parsing import safe_json_parse


def determine_intent(state: AgentState) -> Dict:
    user_input = state.get("user_input", "")
    messages = state.get("messages", [])
    
    if not user_input:
        return {"error": "No user input provided"}
    
    try:
        llm = get_llm(temperature=0.0)
        
        system_prompt = """You are an intent classifier for a coding agent. Analyze the user's request and determine the appropriate action.

Available actions:
- "chat": General conversation, questions, greetings (DEFAULT for non-action queries)
- "edit": Edit or create a single file
- "edit_multi": Edit multiple EXISTING files (e.g., "add type hints to utils.py and main.py")
- "project": Create multiple NEW files (e.g., "create 5 files", "build a website", "scaffold a project")
- "shell": Run a shell command
- "review": Review code changes (PR review, code review, diff review)
- "remember": Save information to long-term memory
- "recall": Retrieve information from long-term memory

IMPORTANT: Use "chat" for:
- Questions (how, what, why, can you, etc.)
- Greetings (hello, hi, hey)
- Clarifications
- General conversation

Use "edit" for:
- Single file editing or creation
- "write it to [filename]" or "save it as [filename]" when referring to previously discussed content
- "edit [filename]" or "create [filename]" (single file)

Use "edit_multi" for:
- Editing multiple existing files with the same instruction
- "add type hints to utils.py, main.py, and helpers.py"
- "refactor file1.py and file2.py"
- "update logging in all these files: a.py, b.py, c.py"

Use "project" for:
- Creating multiple NEW files from scratch
- "create 5 files", "write multiple files", "build a website"
- "scaffold a Python project"

Use "shell" for:
- Command execution requests
- "run", "execute", "ls", "grep" or other shell commands

Use "review" for:
- Code review requests
- "review this PR", "review my changes", "check the diff"

Use "remember" for:
- Saving user preferences, facts, or project information
- "remember my name is X", "save that I prefer Y", "remember this project uses Z"

Use "recall" for:
- Retrieving saved information
- "what's my name?", "what do I prefer?", "what did I tell you about X?"

When user says "write it" or "save it", look at conversation history to understand what content they're referring to.

Extract relevant information:
- For "chat": no additional fields needed
- For "edit": extract path and edit_instruction (the content or instruction)
- For "edit_multi": extract paths (array of file paths) and edit_instruction (what to change)
- For "project": extract project_instruction (full description of what to create)
- For "shell": extract command (the shell command to run)
- For "review": extract base_branch and head_branch (optional, defaults to main and HEAD)
- For "remember": extract memory_key (label) and memory_value (dict of info to save)
- For "recall": extract memory_key (what to retrieve)

Respond with valid JSON only:
{
    "action": "chat|edit|edit_multi|project|shell|review|remember|recall",
    "path": "file path" (for edit),
    "paths": ["file1.py", "file2.py"] (for edit_multi),
    "edit_instruction": "what to write or change" (for edit or edit_multi),
    "project_instruction": "full project description" (for project),
    "command": "shell command" (for shell),
    "base_branch": "branch name" (for review, optional),
    "head_branch": "branch name" (for review, optional),
    "memory_key": "key label" (for remember/recall),
    "memory_value": {"key": "value"} (for remember)
}

Examples:
- "hello" → {"action": "chat"}
- "what can you do?" → {"action": "chat"}
- "run ls -la" → {"action": "shell", "command": "ls -la"}
- "review this PR" → {"action": "review"}
- "add a fibonacci function to utils.py" → {"action": "edit", "path": "utils.py", "edit_instruction": "add a fibonacci function"}
- "add type hints to utils.py and main.py" → {"action": "edit_multi", "paths": ["utils.py", "main.py"], "edit_instruction": "add type hints"}
- "refactor logging in file1.py, file2.py, file3.py" → {"action": "edit_multi", "paths": ["file1.py", "file2.py", "file3.py"], "edit_instruction": "refactor logging"}
- "in the anew folder write 5 readme files" → {"action": "project", "project_instruction": "create 5 readme files with random info in the anew folder"}
- "create a website with html css" → {"action": "project", "project_instruction": "create a website with html css"}
- "remember my name is John" → {"action": "remember", "memory_key": "name", "memory_value": {"name": "John"}}
- "what's my name?" → {"action": "recall", "memory_key": "name"}"""

        context_lines = []
        if messages:
            recent_messages = messages[-4:] if len(messages) > 4 else messages
            for msg in recent_messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if len(content) > 200:
                    content = content[:200] + "..."
                context_lines.append(f"{role}: {content}")
        
        context_str = "\n".join(context_lines) if context_lines else "No previous context"
        
        user_prompt = f"""Recent conversation context:
{context_str}

Current user request: {user_input}

Classify the intent and extract parameters as JSON:"""

        response = llm.invoke(prompt=user_prompt, system_prompt=system_prompt)
        intent_data = safe_json_parse(response, default={"action": "chat"})
        
        result = {"action": intent_data.get("action", "chat")}
        
        if "path" in intent_data:
            result["path"] = intent_data["path"]
        
        if "paths" in intent_data:
            result["paths"] = intent_data["paths"]
        
        if "edit_instruction" in intent_data:
            result["edit_instruction"] = intent_data["edit_instruction"]
        
        if "command" in intent_data:
            result["command"] = intent_data["command"]
        
        if "base_branch" in intent_data:
            result["base_branch"] = intent_data["base_branch"]
        
        if "head_branch" in intent_data:
            result["head_branch"] = intent_data["head_branch"]
        
        if "memory_key" in intent_data:
            result["memory_key"] = intent_data["memory_key"]
        
        if "memory_value" in intent_data:
            result["memory_value"] = intent_data["memory_value"]
        
        if "project_instruction" in intent_data:
            result["project_instruction"] = intent_data["project_instruction"]
        
        result["error"] = ""
        return result
        
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse intent: {str(e)}"}
    except Exception as e:
        return {"error": f"Error determining intent: {str(e)}"}


def route_action(state: AgentState) -> str:
    action = state.get("action", "chat")
    
    if action == "edit":
        return "read_file"
    elif action == "edit_multi":
        return "edit_multi"
    elif action == "project":
        return "project"
    elif action == "shell":
        return "shell"
    elif action == "review":
        return "review"
    elif action == "remember":
        return "remember"
    elif action == "recall":
        return "recall"
    
    return "chat"
