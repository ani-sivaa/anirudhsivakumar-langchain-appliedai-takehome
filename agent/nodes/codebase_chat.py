"""
Codebase Chat Node

This module implements RAG (Retrieval-Augmented Generation) for answering
questions about the codebase using LangChain's vector store.

Design decisions:
- Uses LangChain's similarity_search for retrieval
- Simple and clean integration
- LLM generates answers based on retrieved code
- Falls back gracefully if no results found

Architecture:
1. User asks: "how does the graph work?"
2. Vector store finds similar documents (files)
3. LLM reads the code and explains it
4. Return natural language explanation

This is a classic RAG pattern: Retrieve → Generate
"""

from typing import Dict
from agent.state import AgentState
from agent.tools.llm import get_llm
from agent.tools.codebase_indexer import index_codebase, search_codebase


def index_codebase_node(state: AgentState) -> Dict:
    """
    Index the entire codebase for semantic search.

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
            response = f"Indexed {total_files} files for semantic search.\n\n"
            response += "You can now ask questions like:\n"
            response += "- 'how does the graph work?'\n"
            response += "- 'where is error handling?'\n"
            response += "- 'explain the memory system'"

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


def chat_about_codebase(state: AgentState) -> Dict:
    """
    Answer questions about the codebase using RAG.

    Process:
    1. Retrieve: Semantic search finds relevant files
    2. Generate: LLM explains based on code

    Args:
        state: Agent state with user input

    Returns:
        Updated state with response

    Example:
        User: "how does the graph work?"
        1. Search finds agent/graph.py
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
        results = search_codebase(query=user_input, k=5)

        if not results:
            response = "No relevant files found.\n\n"
            response += "Make sure you've indexed the codebase first:\n"
            response += "Say 'index the codebase' to get started."

            return {
                "response": response,
                "messages": [{"role": "assistant", "content": response}]
            }

        # Build context from retrieved documents
        context_parts = ["Here are the relevant files:\n"]

        for i, doc in enumerate(results, 1):
            path = doc.metadata.get('path', 'unknown')
            content = doc.page_content

            context_parts.append(f"\n--- File {i}: {path} ---")

            # Truncate if too long
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

        if "dimension" in str(e).lower():
            error_msg += "\n\nDimension mismatch! Your Pinecone index has wrong dimensions.\n"
            error_msg += "OpenAI text-embedding-ada-002 requires 1536 dimensions.\n\n"
            error_msg += "To fix:\n"
            error_msg += "1. Go to https://app.pinecone.io\n"
            error_msg += "2. Delete your current index\n"
            error_msg += "3. Create new index with 1536 dimensions"
        elif "pinecone" in str(e).lower() or "api_key" in str(e).lower():
            error_msg += "\n\nPinecone not configured.\n"
            error_msg += "Make sure PINECONE_API_KEY is set in .env\n"
            error_msg += "Get API key at: https://app.pinecone.io"

        return {
            "response": error_msg,
            "error": str(e),
            "messages": [{"role": "assistant", "content": error_msg}]
        }
