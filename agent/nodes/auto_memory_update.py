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
        print(f"Auto-memory update failed: {e}")
    
    return state


def recall_project_context(state: AgentState) -> AgentState:
    """
    Retrieves stored project context from memory.
    Checks the codebase index first (from index_codebase), then falls back to auto-memory.
    
    Useful for:
    - "What files exist in this project?"
    - "What's the project structure?"
    - "What did we build so far?"
    """
    try:
        store = get_memory_store()
        user_id = state.get("user_id", "default_user")
        
        # First check if codebase has been indexed
        codebase_index = list(store.search(("codebase", "index")))
        
        if codebase_index:
            # Use the codebase index data
            metadata = codebase_index[0]
            meta_value = metadata.value if hasattr(metadata, 'value') else metadata
            
            # Get all indexed files
            all_files = list(store.search(("codebase", "files")))
            file_paths = [
                (f.value if hasattr(f, 'value') else f).get('path', '')
                for f in all_files
            ]
            
            # Identify key files
            key_files = [f for f in file_paths if any(k in f.lower() for k in 
                        ['readme', 'main.py', 'graph.py', 'state.py', 'requirements', 'package.json'])]
            
            response = f"""
Codebase Overview:

Total Files: {meta_value.get('total_files', 0)} indexed
Total Size: {meta_value.get('total_size', 0):,} bytes
Workspace: {meta_value.get('workspace', 'Unknown')}
Last Indexed: {meta_value.get('indexed_at', 'Unknown')}

Key Files ({len(key_files)} found):
{chr(10).join(f"  - {f}" for f in sorted(key_files)[:15])}

All Files ({len(file_paths)} total):
{chr(10).join(f"  - {f}" for f in sorted(file_paths)[:25])}
{"  ... and more" if len(file_paths) > 25 else ""}

Tip: Use 'search for X' to find specific functionality in the codebase!
"""
            
            return {**state, "response": response}
        
        # Fallback to old auto-memory system
        items = list(store.search(("project", "structure")))
        
        if not items:
            # Neither index exists - suggest indexing
            return {**state, "response": "Codebase not indexed yet. Try: 'index the codebase' to make it searchable!"}
        
        latest = items[0]
        context = latest.value if hasattr(latest, 'value') else latest
        
        response = f"""
Project Context:

Type: {context.get('project_type', 'Unknown')}
Root: {context.get('project_root', 'Unknown')}
Files: {context.get('file_count', 0)} tracked files
Last Scanned: {context.get('last_updated', 'Just now')}

Key Files:
{chr(10).join(f"  - {f}" for f in context.get('key_files', [])[:10])}

All Files ({len(context.get('all_files', []))} total):
{chr(10).join(f"  - {f}" for f in sorted(context.get('all_files', []))[:20])}
{"  ... and more" if len(context.get('all_files', [])) > 20 else ""}
"""
        
        return {**state, "response": response}
    
    except Exception as e:
        return {**state, "response": f"Error retrieving project context: {str(e)}"}

