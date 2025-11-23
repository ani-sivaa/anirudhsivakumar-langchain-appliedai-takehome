"""
Pinecone Vector Store using LangChain

This module provides a proper LangChain-Pinecone integration for semantic search.

Design decisions:
- Uses langchain-pinecone for native LangChain integration
- Pinecone stores document embeddings for semantic search
- OpenAI text-embedding-ada-002 (1536 dimensions)
- Not used for conversation memory (LangGraph handles that)
- Used specifically for document/code semantic search

Architecture:
- PineconeVectorStore from LangChain handles embedding + storage
- Documents are embedded and stored automatically
- Semantic search via similarity_search() method
"""

import os
from typing import List, Optional, Dict
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document


def get_pinecone_vector_store(
    index_name: Optional[str] = None,
    namespace: str = "codebase"
) -> PineconeVectorStore:
    """
    Get or create a LangChain PineconeVectorStore.

    This uses the proper LangChain integration for Pinecone.

    Args:
        index_name: Name of Pinecone index (defaults to env var)
        namespace: Namespace for organizing vectors

    Returns:
        PineconeVectorStore instance ready for semantic search

    Example:
        vector_store = get_pinecone_vector_store()

        # Add documents
        vector_store.add_documents([
            Document(page_content="code here", metadata={"path": "file.py"})
        ])

        # Search
        results = vector_store.similarity_search("how does X work?", k=5)
    """
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY not found in environment")

    # Get index name from env or use provided
    if index_name is None:
        index_name = os.getenv("PINECONE_INDEX_NAME", "langchain-take-home")

    # Initialize Pinecone client
    pc = Pinecone(api_key=api_key)

    # Get the index
    try:
        index = pc.Index(index_name)

        # Verify index exists and check dimensions
        stats = index.describe_index_stats()
        if stats.dimension != 1536:
            raise ValueError(
                f"Index dimension is {stats.dimension}, expected 1536. "
                f"OpenAI text-embedding-ada-002 requires 1536 dimensions. "
                f"Please recreate your Pinecone index with correct dimensions."
            )
    except Exception as e:
        raise ValueError(f"Could not connect to Pinecone index '{index_name}': {e}")

    # Initialize OpenAI embeddings
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

    # Create LangChain vector store
    vector_store = PineconeVectorStore(
        index=index,
        embedding=embeddings,
        namespace=namespace
    )

    return vector_store


_vector_store: Optional[PineconeVectorStore] = None


# Cache stores by namespace
_vector_stores: Dict[str, PineconeVectorStore] = {}


def get_cached_vector_store(namespace: str = "codebase") -> PineconeVectorStore:
    """
    Get cached vector store instance (singleton pattern per namespace).

    This ensures we reuse the same connection throughout the app.
    Different namespaces get different cached instances.
    """
    global _vector_stores

    if namespace not in _vector_stores:
        _vector_stores[namespace] = get_pinecone_vector_store(namespace=namespace)

    return _vector_stores[namespace]
