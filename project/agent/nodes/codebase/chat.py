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
from agent.tools.llm.wrapper import get_llm
from agent.tools.code.indexer import search_codebase


async def chat_about_codebase(state: AgentState) -> Dict:
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
    # Use codebase_query if provided (from multi-step tasks), otherwise fall back to user_input
    query = state.get("codebase_query") or state.get("user_input", "")

    if not query:
        return {
            "response": "No question provided",
            "error": "No user input"
        }

    try:
        # Semantic search for relevant code chunks
        # Include agent-generated-code to search user-created files
        from langchain_core.vectorstores import VectorStore

        # Get vector store for similarity search with scores
        from agent.tools.memory.pinecone_store import get_cached_vector_store, get_pinecone_vector_store

        vector_store = get_cached_vector_store(namespace="codebase")
        results_with_scores = vector_store.similarity_search_with_relevance_scores(query, k=15)

        # Also search agent-generated-code if needed
        agent_results_with_scores = []
        try:
            agent_store = get_pinecone_vector_store(namespace="agent-generated-code")
            agent_results_with_scores = agent_store.similarity_search_with_relevance_scores(query, k=10)
        except:
            pass

        # Combine and sort by relevance score
        all_results = results_with_scores + agent_results_with_scores
        all_results.sort(key=lambda x: x[1], reverse=True)

        # Filter by relevance threshold (0.7 for semantic similarity)
        # Higher scores = more relevant
        filtered_results = [(doc, score) for doc, score in all_results if score > 0.7]

        # If no high-quality results, lower threshold slightly
        if not filtered_results:
            filtered_results = [(doc, score) for doc, score in all_results if score > 0.6]

        # Take top 8 most relevant chunks
        results = [doc for doc, score in filtered_results[:8]]

        if not results:
            response = "No relevant code found.\n\n"
            response += "Make sure you've indexed the codebase first:\n"
            response += "Say 'index the codebase' to get started."

            return {
                "response": response,
                "messages": [{"role": "assistant", "content": response}]
            }

        # Build context from retrieved documents with better organization
        context_parts = []

        # Group results by file for better context
        files_dict = {}
        for doc in results:
            path = doc.metadata.get('path', 'unknown')
            if path not in files_dict:
                files_dict[path] = []
            files_dict[path].append(doc)

        # Build organized context
        for file_path, docs in files_dict.items():
            context_parts.append(f"\n{'='*80}")
            context_parts.append(f"FILE: {file_path}")
            context_parts.append(f"{'='*80}\n")

            for doc in docs:
                chunk_type = doc.metadata.get('chunk_type', 'unknown')
                name = doc.metadata.get('name', '')
                content = doc.page_content

                # Build rich header based on chunk type
                if chunk_type == 'function':
                    args = doc.metadata.get('args', [])
                    start_line = doc.metadata.get('start_line', '?')
                    header = f"\n## Function: `{name}({', '.join(args)})` (line {start_line})"
                    docstring = doc.metadata.get('docstring', '')
                    if docstring:
                        header += f"\n**Purpose:** {docstring[:150]}"
                elif chunk_type == 'class':
                    methods = doc.metadata.get('methods', [])
                    start_line = doc.metadata.get('start_line', '?')
                    header = f"\n## Class: `{name}` (line {start_line})"
                    if methods:
                        header += f"\n**Methods:** {', '.join(methods[:10])}"
                    docstring = doc.metadata.get('docstring', '')
                    if docstring:
                        header += f"\n**Purpose:** {docstring[:150]}"
                elif chunk_type == 'module':
                    imports = doc.metadata.get('imports', [])
                    header = f"\n## Module-level code"
                    if imports:
                        header += f"\n**Imports:** {', '.join(imports[:5])}"
                else:
                    header = f"\n## Code Section"

                context_parts.append(header)
                context_parts.append("\n```python")

                # Don't truncate - show full content for better understanding
                # Limit is already enforced by chunking strategy
                context_parts.append(content[:5000])  # Increased limit
                context_parts.append("```\n")

        context = "\n".join(context_parts)

        # Generate answer using LLM
        llm = get_llm(temperature=0.3)  # Slightly higher for better explanations

        system_prompt = """You are an expert code analyst that provides clear, well-structured explanations of codebases.

**Your Output Format:**

Always structure your response using this markdown format:

# Overview
[Provide a 2-3 sentence high-level summary answering the user's question]

# Key Components
[Break down the relevant functions/classes/modules with clear explanations]
- Use bullet points or numbered lists
- Reference specific file paths and line numbers
- Explain what each component does and how they relate

# Implementation Details
[Dive into important code snippets, logic, or design patterns]
- Quote relevant code sections
- Explain the "why" not just the "what"
- Highlight any interesting patterns or techniques

# Summary
[Conclude with a brief synthesis that directly answers the user's question]

**Guidelines:**
- Use proper markdown formatting (headers, code blocks, lists, bold/italic)
- Reference specific locations: `function_name()` in `path/to/file.py:123`
- Show code snippets in backticks or code blocks
- Connect the pieces - explain how components work together
- Be clear and concise - avoid unnecessary verbosity
- If the code doesn't fully answer the question, explicitly state what's missing"""

        user_prompt = f"""Based on the following code from the codebase, please answer the user's question.

The code has been organized by file for better context. Each section shows relevant functions, classes, or modules.

{context}

{'='*80}
**User's Question:** {query}
{'='*80}

Please provide a well-structured, comprehensive answer following the format specified in your system prompt."""

        response = await llm.ainvoke(prompt=user_prompt, system_prompt=system_prompt)

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

