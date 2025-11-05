"""
Codebase Chat Node

This module implements RAG (Retrieval-Augmented Generation) for answering
questions about the codebase.

Design decisions:
- Uses semantic search to find relevant files
- Retrieves top 5 most relevant files
- Provides file content to LLM as context
- LLM generates natural language explanation
- Falls back gracefully if Pinecone not configured

Architecture:
1. User asks: "how does the graph work?"
2. Semantic search finds relevant files (agent/graph.py, etc.)
3. File contents are retrieved from SQLite
4. LLM reads the code and explains it in natural language

This is a classic RAG pattern: Retrieve → Generate
"""

from typing import Dict
from agent.state import AgentState
from agent.tools.llm import get_llm
from agent.tools.codebase_indexer import index_codebase, search_codebase


def index_codebase_node(state: AgentState) -> Dict:
    """
    Index the entire codebase for semantic search.

    This node is called when user requests to index the codebase.

    Args:
        state: Agent state

    Returns:
        Updated state with response message
    """
    try:
        # Get workspace root (default to current directory)
        workspace = state.get("workspace", ".")

        # Index the codebase
        result = index_codebase(workspace)

        if "error" in result:
            response = f"Error indexing codebase: {result['error']}"
        else:
            total_files = result.get("total_files", 0)
            total_size = result.get("total_size", 0)

            response = f"Indexed {total_files} files ({total_size:,} bytes)\n\n"
            response += "You can now ask questions about the codebase using semantic search.\n\n"
            response += "Try asking:\n"
            response += "- 'how does the graph work?'\n"
            response += "- 'where is error handling implemented?'\n"
            response += "- 'explain the memory system'"

        return {
            "response": response,
            "messages": [{"role": "assistant", "content": response}]
        }

    except Exception as e:
        error_msg = f"Error indexing codebase: {str(e)}"

        # Check for common Pinecone errors
        if "dimension" in str(e).lower():
            error_msg += "\n\nDimension mismatch detected. Your Pinecone index may have the wrong dimensions.\n"
            error_msg += "OpenAI text-embedding-ada-002 requires 1536 dimensions.\n\n"
            error_msg += "To fix:\n"
            error_msg += "1. Go to https://app.pinecone.io\n"
            error_msg += "2. Delete your current index\n"
            error_msg += "3. Restart the agent (it will create a new index with correct dimensions)"

        return {
            "response": error_msg,
            "error": str(e),
            "messages": [{"role": "assistant", "content": error_msg}]
        }


def chat_about_codebase(state: AgentState) -> Dict:
    """
    Answer questions about the codebase using semantic search and LLM.

    This implements the RAG pattern:
    1. Retrieve: Use semantic search to find relevant files
    2. Augment: Provide file contents as context
    3. Generate: LLM explains based on the code

    Args:
        state: Agent state with user input

    Returns:
        Updated state with response message

    Example:
        User: "how does the graph work?"
        1. Semantic search finds: agent/graph.py, agent/state.py
        2. LLM reads the code
        3. LLM explains: "The graph uses LangGraph's StateGraph..."
    """
    user_input = state.get("user_input", "")

    if not user_input:
        return {
            "response": "No question provided",
            "error": "No user input"
        }

    try:
        # Semantic search for relevant files
        results = search_codebase(query=user_input, limit=5)

        if not results:
            response = "No relevant files found in the codebase.\n\n"
            response += "Make sure you've indexed the codebase first by saying:\n"
            response += "'index the codebase' or 'index project files'"

            return {
                "response": response,
                "messages": [{"role": "assistant", "content": response}]
            }

        # Build context from retrieved files
        context_parts = []
        context_parts.append("Here are the relevant files I found:\n")

        for i, file_data in enumerate(results, 1):
            metadata = file_data.get('metadata', {})
            path = metadata.get('path', 'unknown')
            content = file_data.get('content', '')
            score = file_data.get('score', 0.0)

            context_parts.append(f"\n--- File {i}: {path} (relevance: {score:.2f}) ---")

            # Truncate content if too long (keep first 1500 chars)
            if len(content) > 1500:
                content = content[:1500] + "\n... (truncated)"

            context_parts.append(content)

        context = "\n".join(context_parts)

        # Generate answer using LLM
        llm = get_llm(temperature=0.2)

        system_prompt = """You are a helpful coding assistant that explains codebases.

You have been provided with relevant files from a codebase. Your job is to answer
the user's question based on the code you see.

Be specific and reference file names and code snippets when explaining.
If the code doesn't fully answer the question, say so and explain what you can.

Keep your explanation clear and concise."""

        user_prompt = f"""Based on these files from the codebase:

{context}

---

Please answer this question:
{user_input}"""

        response = llm.invoke(prompt=user_prompt, system_prompt=system_prompt)

        return {
            "response": response,
            "messages": [{"role": "assistant", "content": response}],
            "error": ""
        }

    except Exception as e:
        error_msg = f"Error searching codebase: {str(e)}"

        # Check for common Pinecone errors
        if "dimension" in str(e).lower():
            error_msg += "\n\nDimension mismatch detected. Your Pinecone index may have the wrong dimensions.\n"
            error_msg += "OpenAI text-embedding-ada-002 requires 1536 dimensions.\n\n"
            error_msg += "To fix:\n"
            error_msg += "1. Go to https://app.pinecone.io\n"
            error_msg += "2. Delete your current index\n"
            error_msg += "3. Restart the agent (it will create a new index with correct dimensions)"
        elif "pinecone" in str(e).lower() or "api_key" in str(e).lower():
            error_msg += "\n\nPinecone not configured properly.\n"
            error_msg += "Make sure PINECONE_API_KEY is set in your .env file.\n"
            error_msg += "Get your API key at: https://app.pinecone.io"

        return {
            "response": error_msg,
            "error": str(e),
            "messages": [{"role": "assistant", "content": error_msg}]
        }
