"""
Node that automatically updates long-term memory with project context.
Runs after file operations to keep the agent's memory fresh.
"""

from agent.state import AgentState
from agent.tools.memory import get_memory_store
from agent.tools.auto_memory import build_project_memory, should_auto_update_memory
from langgraph.store.base import Item


def auto_update_project_memory(state: AgentState) -> AgentState:
    """
    Automatically captures and updates project structure in long-term memory.
    
    This runs after file edits/project creation to keep the agent aware of:
    - What files exist
    - Project structure
    - Key files and their purposes
    
    Silent operation - doesn't add to response unless there's an issue.
    """
    action = state.get("action")
    
    # Only auto-update after certain actions
    if not should_auto_update_memory(action):
        return state
    
    try:
        store = get_memory_store()
        memory_data = build_project_memory(state.get("user_id", "default_user"))
        
        # Store in long-term memory
        store.put(
            namespace=tuple(memory_data['namespace']),
            key="current_structure",
            value=memory_data['memory']
        )
        
        # Also store individual file tracking for quick lookups
        for file_path in memory_data['memory']['key_files']:
            store.put(
                namespace=("project", "files"),
                key=file_path,
                value={
                    "path": file_path,
                    "tracked_at": memory_data['memory']['last_updated'],
                    "status": "active"
                }
            )
        
    except Exception as e:
        # Silent failure - don't break the workflow if memory update fails
        pass

    return state


def recall_project_context(state: AgentState) -> AgentState:
    """
    Retrieves stored project context from memory.
    
    Useful for:
    - "What files exist in this project?"
    - "What's the project structure?"
    - "What did we build so far?"
    """
    try:
        store = get_memory_store()
        user_id = state.get("user_id", "default_user")
        
        # Get current project structure from memory
        items = store.search(namespace=("project", "structure"))
        
        if items:
            latest = items[0]  # Most recent
            context = latest.get('value') if isinstance(latest, dict) else latest
            
            response = f"""
Project Context (from memory):

Type: {context.get('project_type', 'Unknown')}
Root: {context.get('project_root', 'Unknown')}
Files: {context.get('file_count', 0)} tracked files
Last Updated: {context.get('last_updated', 'Never')}

Key Files:
{chr(10).join(f"  - {f}" for f in context.get('key_files', [])[:10])}

All Files ({len(context.get('all_files', []))} total):
{chr(10).join(f"  - {f}" for f in sorted(context.get('all_files', []))[:20])}
{"  ... and more" if len(context.get('all_files', [])) > 20 else ""}
"""
            
            return {**state, "response": response}
        else:
            return {**state, "response": "No project context found in memory yet. I'll start tracking it after you edit or create files."}
    
    except Exception as e:
        return {**state, "response": f"Error retrieving project context: {str(e)}"}

