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
        
        # Convert to list of dicts
        all_file_data = []
        for item in all_files:
            if hasattr(item, 'value'):
                all_file_data.append(item.value)
            elif isinstance(item, dict):
                all_file_data.append(item)
            else:
                # Debug: print what we got
                print(f"DEBUG: Unexpected item type: {type(item)}, value: {item}")
        
        # Filter out None values
        all_file_data = [f for f in all_file_data if f is not None]
        
        # For general questions, prioritize key files
        general_questions = ['what', 'tell me', 'explain', 'describe', 'overview', 'about']
        is_general = any(q in query.lower() for q in general_questions)
        
        if is_general:
            # For general questions, grab README + key project files
            priority_patterns = ['readme', 'graph.py', 'state.py', 'main.py', 'requirements']
            top_files = [f for f in all_file_data if any(p in f.get('path', '').lower() for p in priority_patterns)]
            
            # If no priority files, just take first 5
            if not top_files:
                top_files = all_file_data[:5]
            else:
                top_files = top_files[:5]
        else:
            # For specific queries, search based on keywords
            keywords = [w for w in query.lower().split() if len(w) > 3]
            
            matching_files = []
            for file_data in all_file_data:
                searchable = f"{file_data.get('path', '')} {file_data.get('summary', '')} {file_data.get('content', '')}".lower()
                
                # Score based on keyword matches
                score = sum(1 for keyword in keywords if keyword in searchable)
                
                if score > 0:
                    matching_files.append((score, file_data))
            
            # Sort by score and take top results
            matching_files.sort(reverse=True, key=lambda x: x[0])
            top_files = [f[1] for f in matching_files[:5]]
            
            if not top_files:
                # Fallback to key files if no matches
                priority_patterns = ['readme', 'graph.py', 'state.py']
                top_files = [f for f in all_file_data if any(p in f.get('path', '').lower() for p in priority_patterns)][:3]
        
        # Ensure we have something to show
        if not top_files:
            top_files = all_file_data[:5]
        
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
        response = f"{explanation}\n\n"
        response += f"Files examined:\n"
        for f in top_files:
            response += f"  - {f.get('path')} ({f.get('lines')} lines)\n"
        
        return {**state, "response": response}
    
    except Exception as e:
        return {**state, "response": f"Error searching codebase: {str(e)}"}

