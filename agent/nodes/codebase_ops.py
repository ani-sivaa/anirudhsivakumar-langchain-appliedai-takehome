"""
Codebase operations nodes - index and search the codebase.
"""

from agent.state import AgentState
from agent.tools.memory import get_memory_store
from agent.tools.codebase_indexer import index_codebase, store_codebase_index, search_codebase
from typing import Dict


def index_codebase_node(state: AgentState) -> AgentState:
    """
    Index the entire codebase and store in long-term memory.
    This makes the codebase searchable.
    """
    try:
        store = get_memory_store()
        user_id = state.get("user_id", "default_user")
        
        # Index the codebase
        index_data = index_codebase()
        
        # Store in long-term memory
        store_codebase_index(store, index_data, user_id)
        
        response = f"""
Codebase indexed successfully!

Total files indexed: {index_data['total_files']}
Total code size: {index_data['total_size']:,} bytes
Workspace: {index_data['workspace']}

The codebase is now searchable. You can ask me about specific files or functionality.
"""
        
        return {**state, "response": response}
    
    except Exception as e:
        return {**state, "response": f"Error indexing codebase: {str(e)}"}


def search_codebase_node(state: AgentState) -> AgentState:
    """
    Search the indexed codebase for relevant files.
    Uses the user's query to find matching code.
    """
    try:
        store = get_memory_store()
        query = state.get("user_input", "")
        
        # Search the codebase
        matching_files = search_codebase(store, query)
        
        if not matching_files:
            return {**state, "response": "No matching files found. Try indexing the codebase first with: 'index the codebase'"}
        
        # Format results
        response_lines = [f"Found {len(matching_files)} matching files:\n"]
        
        for file_data in matching_files[:10]:  # Show top 10
            response_lines.append(f"\nFile: {file_data.get('path')}")
            response_lines.append(f"  Lines: {file_data.get('lines')}")
            response_lines.append(f"  Summary: {file_data.get('summary', 'N/A')[:200]}")
        
        if len(matching_files) > 10:
            response_lines.append(f"\n... and {len(matching_files) - 10} more files")
        
        return {**state, "response": '\n'.join(response_lines)}
    
    except Exception as e:
        return {**state, "response": f"Error searching codebase: {str(e)}"}

