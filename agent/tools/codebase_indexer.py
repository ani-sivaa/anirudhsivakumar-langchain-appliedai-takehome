"""
Codebase Indexer using LangChain Documents

This module indexes codebase files as LangChain Documents for semantic search.

Design decisions:
- Converts files to LangChain Document objects
- Filters out common non-code files
- Extracts docstrings from Python files
- Stores in Pinecone via LangChain vector store
- Simple and clean integration with LangChain ecosystem

Architecture:
- Walk directory tree
- Convert each file to Document(page_content=code, metadata={path, type})
- Use vector_store.add_documents() to embed and store
"""

import os
import ast
from pathlib import Path
from typing import List, Dict, Any, Optional

from langchain_core.documents import Document
from agent.tools.pinecone_store import get_cached_vector_store


# Files and directories to skip
IGNORE_PATTERNS = {
    ".git", ".svn", ".hg",
    "node_modules", "venv", ".venv", "env", ".env",
    "__pycache__", ".pytest_cache", ".mypy_cache",
    "site-packages", "dist", "build", ".eggs",
    ".idea", ".vscode", ".vs",
    "data", ".DS_Store",
    "context"
}

# File extensions to index
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".java", ".cpp", ".c", ".h", ".hpp",
    ".go", ".rs", ".rb", ".php",
    ".md", ".txt", ".yaml", ".yml", ".json",
    ".sh", ".bash"
}


def should_index_file(file_path: Path) -> bool:
    """Check if file should be indexed."""
    # Skip ignored directories
    for part in file_path.parts:
        if part in IGNORE_PATTERNS or part.startswith("."):
            return False

    # Check extension
    if file_path.suffix not in CODE_EXTENSIONS:
        return False

    # Skip large files (> 1MB)
    try:
        if file_path.stat().st_size > 1_000_000:
            return False
    except:
        return False

    return True


def extract_python_summary(file_path: Path) -> Optional[str]:
    """Extract module docstring from Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
        docstring = ast.get_docstring(tree)
        if docstring:
            return docstring.split("\n\n")[0].strip()
    except:
        pass
    return None


def file_to_document(file_path: Path, workspace_root: Path) -> Optional[Document]:
    """
    Convert a file to a LangChain Document.

    Args:
        file_path: Absolute path to file
        workspace_root: Absolute path to workspace root

    Returns:
        Document with page_content (file contents) and metadata
    """
    try:
        # Read file
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Get relative path
        rel_path = str(file_path.relative_to(workspace_root))

        # Extract summary for metadata
        summary = None
        if file_path.suffix == ".py":
            summary = extract_python_summary(file_path)

        # Create Document
        metadata = {
            "path": rel_path,
            "type": file_path.suffix[1:],
            "size": len(content)
        }

        if summary:
            metadata["summary"] = summary

        doc = Document(
            page_content=content,
            metadata=metadata
        )

        return doc

    except Exception as e:
        return None


def index_codebase(workspace_root: str = ".") -> Dict[str, Any]:
    """
    Index entire codebase for semantic search.

    Walks through files, converts to Documents, and stores in Pinecone.

    Args:
        workspace_root: Path to workspace root (default: current directory)

    Returns:
        Dict with indexing results

    Example:
        result = index_codebase(".")
        print(f"Indexed {result['total_files']} files")
    """
    workspace_path = Path(workspace_root).resolve()

    if not workspace_path.exists():
        return {
            "error": f"Workspace not found: {workspace_path}",
            "total_files": 0
        }

    # Collect all documents
    documents = []

    for file_path in workspace_path.rglob('*'):
        if not file_path.is_file():
            continue

        if not should_index_file(file_path):
            continue

        doc = file_to_document(file_path, workspace_path)
        if doc:
            documents.append(doc)

    if not documents:
        return {
            "error": "No files found to index",
            "total_files": 0
        }

    try:
        # Get vector store
        vector_store = get_cached_vector_store(namespace="codebase")

        # Add all documents (LangChain handles embedding + storage)
        vector_store.add_documents(documents)

        return {
            'total_files': len(documents),
            'workspace': str(workspace_path)
        }

    except Exception as e:
        error_msg = f"Error indexing documents: {str(e)}"

        return {
            "error": error_msg,
            "total_files": 0
        }


def search_codebase(query: str, k: int = 5) -> List[Document]:
    """
    Semantic search over indexed codebase.

    Args:
        query: Natural language query
        k: Number of results to return

    Returns:
        List of matching Documents with content and metadata

    Example:
        results = search_codebase("how does the graph work?", k=3)
        for doc in results:
            print(f"File: {doc.metadata['path']}")
            print(f"Content: {doc.page_content[:200]}")
    """
    try:
        vector_store = get_cached_vector_store(namespace="codebase")
        results = vector_store.similarity_search(query, k=k)
        return results
    except Exception as e:
        return []
