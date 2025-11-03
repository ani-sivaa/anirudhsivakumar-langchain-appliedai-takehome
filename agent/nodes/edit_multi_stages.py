from typing import Dict

from agent.state import AgentState


def edit_multi_modify_passthrough(state: AgentState) -> Dict:
    """Passthrough between read and modify stages - waits for all reads to complete."""
    return {}


def edit_multi_write_passthrough(state: AgentState) -> Dict:
    """Passthrough between modify and write stages - waits for all modifies to complete."""
    return {}

