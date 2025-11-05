"""
Pinecone Vector Store Wrapper

This module provides a wrapper around the Pinecone client for vector storage and similarity search.

Design decisions:
- Uses Pinecone Serverless (no pod management required)
- Validates dimension compatibility (must match embedding model - 1536 for ada-002)
- Supports namespaces for organizing different types of data
- Provides batch upsert for efficient bulk operations
- Cosine similarity metric for semantic search

Architecture:
- Pinecone stores only vectors + minimal metadata (IDs)
- Content is stored in SQLite (see semantic_memory.py)
- This separation allows fast vector search while keeping costs low
"""

import os
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec


class PineconeVectorStore:
    """
    Wrapper for Pinecone vector database.

    Handles connection, indexing, and similarity search for embeddings.
    Works with OpenAI text-embedding-ada-002 (1536 dimensions).
    """

    def __init__(
        self,
        index_name: str = "langchain-take-home",
        namespace: str = "default",
        dimension: int = 1536,
        metric: str = "cosine"
    ):
        """
        Initialize Pinecone connection.

        Args:
            index_name: Name of the Pinecone index to use
            namespace: Namespace within the index (for organizing data)
            dimension: Vector dimension (must match embedding model - 1536 for ada-002)
            metric: Distance metric (cosine, euclidean, or dotproduct)
        """
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY not found in environment")

        self.index_name = os.getenv("PINECONE_INDEX_NAME", index_name)
        self.namespace = namespace
        self.dimension = dimension
        self.metric = metric

        self.pc = Pinecone(api_key=api_key)

        # Check if index exists, create if needed
        if self.index_name not in [idx.name for idx in self.pc.list_indexes()]:
            print(f"Creating new Pinecone index: {self.index_name}")
            self.pc.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric=self.metric,
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )

        self.index = self.pc.Index(self.index_name)

        # Verify dimension matches
        try:
            stats = self.index.describe_index_stats()
            actual_dim = stats.dimension

            if actual_dim != self.dimension:
                print(f"\nWARNING: Pinecone index dimension mismatch!")
                print(f"   Expected: {self.dimension} (text-embedding-ada-002)")
                print(f"   Actual: {actual_dim}")
                print(f"\nTo fix this:")
                print(f"   1. Delete the index at https://app.pinecone.io")
                print(f"   2. Restart the agent (it will create a new index with correct dimensions)")
                print()
        except Exception as e:
            print(f"Warning: Could not verify index dimensions: {e}")

    def upsert(
        self,
        vectors: List[Dict[str, Any]],
        namespace: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Insert or update vectors in Pinecone.

        Args:
            vectors: List of dicts with 'id', 'values' (vector), and optional 'metadata'
            namespace: Override the default namespace

        Returns:
            Dict with upsert count

        Example:
            store.upsert([
                {
                    "id": "file_1",
                    "values": [0.1, 0.2, ...],  # 1536 dimensions
                    "metadata": {"path": "agent/graph.py"}
                }
            ])
        """
        ns = namespace or self.namespace

        try:
            response = self.index.upsert(
                vectors=vectors,
                namespace=ns
            )
            return {"upserted_count": response.upserted_count}
        except Exception as e:
            print(f"Error upserting to Pinecone: {e}")
            raise

    def query(
        self,
        vector: List[float],
        top_k: int = 5,
        namespace: Optional[str] = None,
        filter: Optional[Dict] = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.

        Args:
            vector: Query vector (1536 dimensions for ada-002)
            top_k: Number of results to return
            namespace: Override the default namespace
            filter: Metadata filter (e.g., {"type": "python_file"})
            include_metadata: Whether to include metadata in results

        Returns:
            List of matches with 'id', 'score', and optional 'metadata'

        Example:
            results = store.query(
                vector=query_embedding,
                top_k=5,
                filter={"type": "python_file"}
            )
        """
        ns = namespace or self.namespace

        try:
            response = self.index.query(
                vector=vector,
                top_k=top_k,
                namespace=ns,
                filter=filter,
                include_metadata=include_metadata
            )

            results = []
            for match in response.matches:
                result = {
                    "id": match.id,
                    "score": match.score
                }
                if include_metadata and hasattr(match, 'metadata'):
                    result["metadata"] = match.metadata
                results.append(result)

            return results

        except Exception as e:
            print(f"Error querying Pinecone: {e}")
            raise

    def delete(
        self,
        ids: Optional[List[str]] = None,
        namespace: Optional[str] = None,
        delete_all: bool = False
    ):
        """
        Delete vectors from Pinecone.

        Args:
            ids: List of vector IDs to delete
            namespace: Override the default namespace
            delete_all: If True, delete all vectors in namespace
        """
        ns = namespace or self.namespace

        try:
            if delete_all:
                self.index.delete(delete_all=True, namespace=ns)
            elif ids:
                self.index.delete(ids=ids, namespace=ns)
        except Exception as e:
            print(f"Error deleting from Pinecone: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """
        Get index statistics.

        Returns:
            Dict with dimension, index_fullness, namespaces, and total_vector_count
        """
        try:
            stats = self.index.describe_index_stats()
            return {
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
                "namespaces": stats.namespaces,
                "total_vector_count": stats.total_vector_count
            }
        except Exception as e:
            print(f"Error getting Pinecone stats: {e}")
            return {}


_pinecone_store: Optional[PineconeVectorStore] = None


def get_pinecone_store(
    index_name: str = "langchain-take-home",
    namespace: str = "default"
) -> PineconeVectorStore:
    """
    Get or create a singleton Pinecone store instance.

    This ensures we only create one connection to Pinecone throughout the app.
    """
    global _pinecone_store

    if _pinecone_store is None:
        _pinecone_store = PineconeVectorStore(
            index_name=index_name,
            namespace=namespace
        )

    return _pinecone_store
