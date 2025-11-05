"""
Semantic Memory Store

This module implements a hybrid semantic memory system using:
1. Pinecone for vector embeddings (fast similarity search)
2. SQLite for content storage (fast local access)

Design decisions:
- Hybrid architecture: Pinecone stores vectors, SQLite stores content
- Fallback strategy: If Pinecone unavailable, falls back to SQLite-only
- Uses OpenAI text-embedding-ada-002 (1536 dimensions)
- Namespaces organize different data types (codebase, facts, etc.)
- Search returns full content from SQLite, not just vectors

Architecture flow:
1. Store: Content → SQLite, Embedding → Pinecone
2. Search: Query → Pinecone (find similar vectors) → Get IDs → SQLite (fetch content)

This design keeps costs low (Pinecone stores only vectors) while maintaining
fast search performance.
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from langchain_openai import OpenAIEmbeddings
from agent.tools.sqlite_store import SQLiteStore
from agent.tools.pinecone_store import get_pinecone_store


class SemanticMemoryStore:
    """
    Hybrid semantic memory: Pinecone for vectors, SQLite for content.

    This store enables semantic search over any text content (code, facts, docs).
    When you search, it finds semantically similar items even if exact words don't match.

    Example:
        store = SemanticMemoryStore()

        # Store codebase file
        store.put(
            namespace=("codebase", "files"),
            key="agent/graph.py",
            value={
                "path": "agent/graph.py",
                "content": "...",
                "metadata": {"type": "python"}
            }
        )

        # Search for similar files
        results = store.search(
            namespace=("codebase", "files"),
            query="how does the graph work?",
            limit=5
        )
    """

    def __init__(self, db_path: str = "./data/long_term_memory.db"):
        """
        Initialize hybrid semantic store.

        Args:
            db_path: Path to SQLite database for content storage
        """
        self.store = SQLiteStore(db_path)

        # Setup Pinecone for vector storage
        try:
            if not os.getenv("PINECONE_API_KEY"):
                print("PINECONE_API_KEY not set in environment")
                print("Falling back to SQLite-only mode (no semantic search)")
                self.use_pinecone = False
            else:
                self.vector_store = get_pinecone_store()
                self.use_pinecone = True
                print("Pinecone vector store connected")
        except Exception as e:
            print(f"Pinecone not available: {e}")
            print("Falling back to SQLite-only mode (no semantic search)")
            self.use_pinecone = False

        # Setup OpenAI embeddings
        try:
            self.embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
            print("Using text-embedding-ada-002 (1536 dimensions)")
        except Exception as e:
            print(f"Warning: Could not initialize OpenAI embeddings: {e}")
            self.embeddings = None
            self.use_pinecone = False

    def _get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text.

        Args:
            text: Text to embed

        Returns:
            List of 1536 floats (vector representation)
        """
        if not self.embeddings:
            raise ValueError("Embeddings not initialized")

        try:
            embedding = self.embeddings.embed_query(text)
            return embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            raise

    def _namespace_to_string(self, namespace: Tuple[str, ...]) -> str:
        """Convert tuple namespace to string for Pinecone."""
        return "/".join(namespace)

    def put(
        self,
        namespace: Tuple[str, ...],
        key: str,
        value: Dict[str, Any]
    ) -> bool:
        """
        Store content with semantic search capability.

        Args:
            namespace: Tuple like ("codebase", "files") or ("memory", "facts")
            key: Unique identifier (e.g., file path)
            value: Dict with content and metadata

        Returns:
            True if stored successfully

        Example:
            store.put(
                namespace=("codebase", "files"),
                key="agent/graph.py",
                value={
                    "path": "agent/graph.py",
                    "content": "# Graph definition...",
                    "metadata": {"type": "python", "lines": 100}
                }
            )
        """
        # Always store in SQLite (source of truth for content)
        self.store.put(namespace, key, value)

        # If Pinecone available, also store embedding
        if self.use_pinecone and self.embeddings:
            try:
                # Extract text for embedding
                content = value.get("content", "")
                if not content:
                    # If no content field, use entire value as text
                    content = str(value)

                # Generate embedding
                embedding = self._get_embedding(content)

                # Store in Pinecone
                vector_data = {
                    "id": f"{self._namespace_to_string(namespace)}::{key}",
                    "values": embedding,
                    "metadata": {
                        "namespace": self._namespace_to_string(namespace),
                        "key": key
                    }
                }

                self.vector_store.upsert(
                    vectors=[vector_data],
                    namespace=self._namespace_to_string(namespace)
                )

            except Exception as e:
                print(f"Warning: Failed to store embedding in Pinecone: {e}")
                print("Content stored in SQLite only")

        return True

    def get(
        self,
        namespace: Tuple[str, ...],
        key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve content by exact key.

        Args:
            namespace: Tuple namespace
            key: Exact key

        Returns:
            Stored value dict or None if not found
        """
        return self.store.get(namespace, key)

    def search(
        self,
        namespace: Tuple[str, ...],
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Semantic search: find similar content based on meaning.

        Args:
            namespace: Tuple namespace to search within
            query: Natural language query
            limit: Max number of results

        Returns:
            List of matching items with content and metadata

        Example:
            results = store.search(
                namespace=("codebase", "files"),
                query="how does error handling work?",
                limit=5
            )

            for item in results:
                print(f"File: {item['metadata']['path']}")
                print(f"Content: {item['content'][:200]}")
        """
        if not self.use_pinecone or not self.embeddings:
            print("Semantic search not available (Pinecone not configured)")
            return []

        try:
            # Generate query embedding
            query_embedding = self._get_embedding(query)

            # Search Pinecone for similar vectors
            matches = self.vector_store.query(
                vector=query_embedding,
                top_k=limit,
                namespace=self._namespace_to_string(namespace),
                include_metadata=True
            )

            # Fetch full content from SQLite
            results = []
            for match in matches:
                metadata = match.get("metadata", {})
                key = metadata.get("key")

                if key:
                    content = self.store.get(namespace, key)
                    if content:
                        results.append({
                            "key": key,
                            "content": content.get("content", ""),
                            "metadata": content.get("metadata", {}),
                            "score": match.get("score", 0.0)
                        })

            return results

        except Exception as e:
            print(f"Error during semantic search: {e}")
            return []

    def list_keys(
        self,
        namespace: Tuple[str, ...],
        prefix: str = ""
    ) -> List[str]:
        """
        List all keys in a namespace.

        Args:
            namespace: Tuple namespace
            prefix: Optional prefix filter

        Returns:
            List of keys
        """
        return self.store.list_namespaces_with_prefix(namespace, prefix)

    def delete(
        self,
        namespace: Tuple[str, ...],
        key: str
    ) -> bool:
        """
        Delete content and its embedding.

        Args:
            namespace: Tuple namespace
            key: Key to delete

        Returns:
            True if deleted successfully
        """
        # Delete from SQLite
        self.store.delete(namespace, key)

        # Delete from Pinecone if available
        if self.use_pinecone:
            try:
                vector_id = f"{self._namespace_to_string(namespace)}::{key}"
                self.vector_store.delete(
                    ids=[vector_id],
                    namespace=self._namespace_to_string(namespace)
                )
            except Exception as e:
                print(f"Warning: Failed to delete from Pinecone: {e}")

        return True

    def clear_namespace(self, namespace: Tuple[str, ...]) -> bool:
        """
        Delete all content in a namespace.

        Args:
            namespace: Tuple namespace to clear

        Returns:
            True if cleared successfully
        """
        # Get all keys
        keys = self.list_keys(namespace)

        # Delete each key
        for key in keys:
            self.delete(namespace, key)

        # Also clear Pinecone namespace if available
        if self.use_pinecone:
            try:
                self.vector_store.delete(
                    namespace=self._namespace_to_string(namespace),
                    delete_all=True
                )
            except Exception as e:
                print(f"Warning: Failed to clear Pinecone namespace: {e}")

        return True


_semantic_store: Optional[SemanticMemoryStore] = None


def get_semantic_store() -> SemanticMemoryStore:
    """
    Get or create singleton semantic memory store.

    This ensures we use the same store instance throughout the app.
    """
    global _semantic_store

    if _semantic_store is None:
        _semantic_store = SemanticMemoryStore()

    return _semantic_store
