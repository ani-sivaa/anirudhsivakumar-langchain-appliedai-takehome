"""
Codebase Indexer

This module indexes a codebase for semantic search.

Design decisions:
- Walks directory tree recursively
- Filters out common non-code files (.git, node_modules, __pycache__, etc.)
- Extracts docstrings and module-level comments from Python files
- Stores file path, content, and metadata in semantic memory
- Supports incremental updates (re-indexes changed files)

Architecture:
- Uses semantic_memory.py for storage (which handles Pinecone + SQLite)
- Indexes files under namespace ("codebase", "files")
- Each file gets a unique key (relative path from workspace root)

This enables semantic search like:
- "how does the graph work?" → finds agent/graph.py
- "where is error handling?" → finds files with try/except blocks
"""

import os
import ast
from pathlib import Path
from typing import Dict, Any, List, Optional

from agent.tools.semantic_memory import get_semantic_store


# Files and directories to skip during indexing
IGNORE_PATTERNS = {
    # Version control
    ".git", ".svn", ".hg",

    # Dependencies
    "node_modules", "venv", ".venv", "env", ".env",
    "__pycache__", ".pytest_cache", ".mypy_cache",
    "site-packages", "dist", "build", ".eggs",

    # IDE
    ".idea", ".vscode", ".vs",

    # Data and temp files
    "data", ".DS_Store", "*.db", "*.sqlite",

    # Large files
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
    """
    Check if a file should be indexed.

    Args:
        file_path: Path to file

    Returns:
        True if file should be indexed
    """
    # Check if any ignored pattern in path
    for part in file_path.parts:
        if part in IGNORE_PATTERNS or part.startswith("."):
            return False

    # Check file extension
    if file_path.suffix not in CODE_EXTENSIONS:
        return False

    # Check if file is too large (> 1MB)
    try:
        if file_path.stat().st_size > 1_000_000:
            return False
    except:
        return False

    return True


def extract_python_docstring(file_path: Path) -> Optional[str]:
    """
    Extract module-level docstring from Python file.

    Args:
        file_path: Path to Python file

    Returns:
        Docstring text or None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)
        docstring = ast.get_docstring(tree)
        return docstring
    except:
        return None


def get_file_summary(file_path: Path) -> str:
    """
    Generate a brief summary of a file for indexing.

    Args:
        file_path: Path to file

    Returns:
        Summary string
    """
    # For Python files, extract docstring
    if file_path.suffix == ".py":
        docstring = extract_python_docstring(file_path)
        if docstring:
            # Use first paragraph of docstring
            first_para = docstring.split("\n\n")[0]
            return first_para.strip()

    # For other files, use file name and extension
    return f"{file_path.stem} ({file_path.suffix})"


def index_file(file_path: Path, workspace_root: Path) -> Optional[Dict[str, Any]]:
    """
    Index a single file.

    Args:
        file_path: Absolute path to file
        workspace_root: Absolute path to workspace root

    Returns:
        Dict with file data or None if failed
    """
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Get relative path (this becomes the key)
        rel_path = str(file_path.relative_to(workspace_root))

        # Generate summary
        summary = get_file_summary(file_path)

        # Prepare metadata
        metadata = {
            "path": rel_path,
            "type": file_path.suffix[1:],  # Extension without dot
            "size": len(content),
            "summary": summary
        }

        # Store in semantic memory
        store = get_semantic_store()
        store.put(
            namespace=("codebase", "files"),
            key=rel_path,
            value={
                "content": content,
                "metadata": metadata
            }
        )

        return {
            "path": rel_path,
            "size": len(content),
            "summary": summary
        }

    except Exception as e:
        print(f"Error indexing {file_path}: {e}")
        return None


def index_codebase(workspace_root: str = ".") -> Dict[str, Any]:
    """
    Index entire codebase for semantic search.

    This walks through all files in the workspace, filters out ignored files,
    and stores them in semantic memory with embeddings.

    Args:
        workspace_root: Path to workspace root (default: current directory)

    Returns:
        Dict with indexing results

    Example:
        result = index_codebase(".")
        print(f"Indexed {result['total_files']} files")
        print(f"Total size: {result['total_size']} bytes")
    """
    workspace_path = Path(workspace_root).resolve()

    if not workspace_path.exists():
        return {
            "error": f"Workspace not found: {workspace_path}",
            "total_files": 0
        }

    print(f"Indexing codebase: {workspace_path}")

    indexed_files = []
    total_size = 0

    # Walk through all files
    for file_path in workspace_path.rglob('*'):
        if not file_path.is_file():
            continue

        if not should_index_file(file_path):
            continue

        # Index the file
        file_data = index_file(file_path, workspace_path)

        if file_data:
            indexed_files.append(file_data)
            total_size += file_data.get("size", 0)
            print(f"  Indexed: {file_data['path']}")

    print(f"\nIndexing complete:")
    print(f"  Total files: {len(indexed_files)}")
    print(f"  Total size: {total_size:,} bytes")

    return {
        'files': indexed_files,
        'total_files': len(indexed_files),
        'total_size': total_size,
        'workspace': str(workspace_path)
    }


def search_codebase(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Semantic search over indexed codebase.

    Args:
        query: Natural language query
        limit: Max number of results

    Returns:
        List of matching files with content and metadata

    Example:
        results = search_codebase("how does the graph work?", limit=3)
        for result in results:
            print(f"File: {result['metadata']['path']}")
            print(f"Score: {result['score']}")
            print(f"Summary: {result['metadata']['summary']}")
    """
    store = get_semantic_store()

    results = store.search(
        namespace=("codebase", "files"),
        query=query,
        limit=limit
    )

    return results


def clear_codebase_index() -> bool:
    """
    Clear all indexed codebase files.

    Returns:
        True if successful
    """
    store = get_semantic_store()
    return store.clear_namespace(("codebase", "files"))
