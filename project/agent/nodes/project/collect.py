from typing import Dict

from agent.state import AgentState


def collect_project_files(state: AgentState) -> Dict:
    """
    Passthrough node that collects all parallel create_file operations.
    Waits for all file creation nodes to complete before proceeding to summarize.
    """
    return {}

