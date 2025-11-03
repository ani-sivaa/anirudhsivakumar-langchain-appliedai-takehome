from typing import Dict

from agent.state import AgentState


def edit_multi_passthrough(state: AgentState) -> Dict:
    """
    Passthrough node for multi-file editing - just returns empty dict.
    The actual work happens in the fan-out nodes.
    State already has paths and edit_instruction from determine_intent.
    """
    # Ensure paths exists
    paths = state.get("paths", [])
    edit_instruction = state.get("edit_instruction", "")
    
    if not paths:
        return {
            "error": "No file paths specified for multi-file edit. Please specify which files to edit.",
            "response": "I need to know which files to edit. Can you specify the file paths?"
        }
    
    if not edit_instruction:
        return {
            "error": "No edit instruction provided",
            "response": "What changes would you like me to make to these files?"
        }
    
    return {"error": ""}

