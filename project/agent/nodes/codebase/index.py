"""
Codebase Index Node

This module implements indexing for semantic search.
"""

from pathlib import Path
from typing import Dict

from agent.state import AgentState
from agent.tools.code.indexer import index_codebase


def index_codebase_node(state: AgentState) -> Dict:
    """
    Index the entire codebase for semantic search.
    Also indexes agent-generated-code folder if it exists.

    Args:
        state: Agent state

    Returns:
        Updated state with response message
    """
    try:
        workspace = state.get("workspace", ".")
        result = index_codebase(workspace)

        if "error" in result:
            response = f"Error indexing codebase: {result['error']}"
        else:
            total_files = result.get("total_files", 0)
            total_chunks = result.get("total_chunks", 0)
            response = f"Indexed {total_chunks} code chunks from {total_files} files.\n\n"

            # Also index agent-generated-code if it exists
            workspace_path = Path(workspace).resolve()
            agent_generated_folder = workspace_path.parent / "agent-generated-code"
            if agent_generated_folder.exists() and agent_generated_folder.is_dir():
                try:
                    agent_result = index_codebase(str(agent_generated_folder), namespace="agent-generated-code")
                    if not agent_result.get("error") and agent_result.get('total_files', 0) > 0:
                        agent_files = agent_result.get('total_files', 0)
                        agent_chunks = agent_result.get('total_chunks', 0)
                        response += f"Also indexed {agent_chunks} chunks from {agent_files} user-created files.\n\n"
                except Exception:
                    pass
            
            response += "Python files are chunked at function/class level for precise semantic search.\n\n"
            response += "You can now ask questions like:\n"
            response += "- 'which node writes to the response state?'\n"
            response += "- 'how does the graph work?'\n"
            response += "- 'where is error handling?'\n"
            response += "- 'explain the memory system'\n"
            response += "- 'how does the calculator work?' (for user-created files)"

        return {
            "response": response,
            "messages": [{"role": "assistant", "content": response}]
        }

    except Exception as e:
        error_msg = f"Error indexing codebase: {str(e)}"

        if "dimension" in str(e).lower():
            error_msg += "\n\nDimension mismatch! Your Pinecone index has wrong dimensions.\n"
            error_msg += "OpenAI text-embedding-ada-002 requires 1536 dimensions.\n\n"
            error_msg += "To fix:\n"
            error_msg += "1. Go to https://app.pinecone.io\n"
            error_msg += "2. Delete your current index\n"
            error_msg += "3. Create new index with 1536 dimensions"

        return {
            "response": error_msg,
            "error": str(e),
            "messages": [{"role": "assistant", "content": error_msg}]
        }

