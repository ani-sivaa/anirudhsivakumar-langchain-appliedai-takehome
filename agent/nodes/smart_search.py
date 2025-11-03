"""
Smart codebase search with LLM-powered explanations.
Instead of just listing files, this reads the code and explains it.
"""

from agent.state import AgentState
from agent.tools.memory import get_memory_store
from agent.tools.llm import get_llm
from typing import Dict


def smart_search_codebase(state: AgentState) -> AgentState:
    """
    Searches indexed codebase AND uses LLM to explain what it found.
    
    Way better than just listing files - actually reads the code and explains it.
    """
    try:
        store = get_memory_store()
        query = state.get("user_input", "")
        
        # Search for relevant files
        all_files = list(store.search(("codebase", "files")))
        
        if not all_files:
            return {**state, "response": "Codebase not indexed yet. Run: 'index the codebase' first!"}
        
        # Find matching files
        matching_files = []
        query_lower = query.lower()
        
        for item in all_files:
            file_data = item.value if hasattr(item, 'value') else item
            searchable = f"{file_data.get('path', '')} {file_data.get('summary', '')} {file_data.get('content', '')}"
            
            if query_lower in searchable.lower():
                matching_files.append(file_data)
        
        # If no matches, try broader search with keywords
        if not matching_files:
            keywords = query_lower.split()
            for item in all_files:
                file_data = item.value if hasattr(item, 'value') else item
                searchable = f"{file_data.get('path', '')} {file_data.get('summary', '')} {file_data.get('content', '')}".lower()
                
                if any(keyword in searchable for keyword in keywords if len(keyword) > 3):
                    matching_files.append(file_data)
        
        # Get top results
        top_files = matching_files[:5]
        
        if not top_files:
            return {**state, "response": f"No files found matching '{query}'. The codebase has {len(all_files)} indexed files."}
        
        # Build context from matching files
        context_parts = []
        for file_data in top_files:
            context_parts.append(f"\nFile: {file_data.get('path')}")
            context_parts.append(f"Summary: {file_data.get('summary', 'N/A')}")
            context_parts.append(f"Content preview:\n{file_data.get('content', '')[:1000]}")
            context_parts.append("-" * 80)
        
        code_context = '\n'.join(context_parts)
        
        # Use LLM to explain the code
        llm = get_llm(temperature=0.3)
        
        system_prompt = f"""You are a code explanation assistant. The user asked: "{query}"

I've searched the codebase and found {len(top_files)} relevant files. Below is the code from those files.

Your job:
1. Read the code carefully
2. Answer the user's question based on what you see in the code
3. Be specific - cite file names and explain what the code actually does
4. If the code shows implementation details, explain them
5. Keep it concise but thorough

Relevant code:
{code_context}
"""
        
        user_prompt = f"Based on the code shown above, {query}"
        
        explanation = llm.invoke(prompt=user_prompt, system_prompt=system_prompt)
        
        # Format final response
        response = f"Found {len(matching_files)} relevant files. Here's what I found:\n\n{explanation}\n\n"
        response += f"Files examined:\n"
        for f in top_files:
            response += f"  - {f.get('path')} ({f.get('lines')} lines)\n"
        
        return {**state, "response": response}
    
    except Exception as e:
        return {**state, "response": f"Error searching codebase: {str(e)}"}

