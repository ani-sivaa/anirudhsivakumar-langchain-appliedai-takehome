import json
from typing import Dict

from agent.state import AgentState
from agent.tools.llm import get_llm


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
- "edit": Edit or create a file

IMPORTANT: Use "chat" for:
- Questions (how, what, why, can you, etc.)
- Greetings (hello, hi, hey)
- Clarifications
- General conversation

Use "edit" for:
- Explicit file editing requests
- "write it to [filename]" or "save it as [filename]" when referring to previously discussed content
- "create [filename]" requests

When user says "write it" or "save it", look at conversation history to understand what content they're referring to.

Extract relevant information:
- For "chat": no additional fields needed
- For "edit": extract path and edit_instruction (the content or instruction)

Respond with valid JSON only:
{
    "action": "chat|edit",
    "path": "file path" (for edit),
    "edit_instruction": "what to write or change" (for edit)
}

Examples:
- "hello" → {"action": "chat"}
- "what can you do?" → {"action": "chat"}
- "write it to anirudh's the goat.md" (after discussing content) → {"action": "edit", "path": "goat.md", "edit_instruction": "write the content from previous conversation"}
- "add a fibonacci function to utils.py" → {"action": "edit", "path": "utils.py", "edit_instruction": "add a fibonacci function"}"""

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
        
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        intent_data = json.loads(response)
        
        result = {"action": intent_data.get("action", "chat")}
        
        if "path" in intent_data:
            result["path"] = intent_data["path"]
        
        if "edit_instruction" in intent_data:
            result["edit_instruction"] = intent_data["edit_instruction"]
        
        result["error"] = ""
        return result
        
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse intent: {str(e)}"}
    except Exception as e:
        return {"error": f"Error determining intent: {str(e)}"}


def route_action(state: AgentState) -> str:
    action = state.get("action", "chat")
    
    if state.get("error"):
        return "end"
    
    if action == "edit":
        return "edit"
    else:
        return "chat"
