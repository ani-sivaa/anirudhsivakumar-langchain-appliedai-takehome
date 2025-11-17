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


def extract_module_context(tree: ast.Module, lines: List[str]) -> dict:
    """
    Extract module-level context (imports, docstrings, constants).
    
    This context will be prepended to each function/class chunk so they're self-contained.
    
    Returns:
        dict with 'content' (str) and 'imports' (list of str)
    """
    context_lines = []
    import_statements = []
    
    # Get module docstring
    module_doc = ast.get_docstring(tree)
    if module_doc:
        context_lines.append(f'"""\n{module_doc}\n"""')
        context_lines.append('')
    
    # Extract imports and module-level constants
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            # Capture import lines
            start = node.lineno - 1
            end = node.end_lineno
            import_lines = lines[start:end]
            import_text = '\n'.join(import_lines)
            context_lines.append(import_text)
            
            # Track imported names for metadata
            if isinstance(node, ast.Import):
                for alias in node.names:
                    import_statements.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                import_statements.append(module)
        
        elif isinstance(node, ast.Assign):
            # Capture module-level constants (UPPERCASE names)
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    start = node.lineno - 1
                    end = node.end_lineno
                    const_lines = lines[start:end]
                    context_lines.append('\n'.join(const_lines))
    
    context_content = '\n'.join(context_lines) if context_lines else ''
    
    return {
        'content': context_content,
        'imports': import_statements
    }


def extract_names_from_node(node: ast.AST) -> dict:
    """
    Extract what this node references (calls, variables, etc).
    
    Returns metadata about dependencies.
    """
    calls = set()
    names = set()
    
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Name):
                calls.add(child.func.id)
            elif isinstance(child.func, ast.Attribute):
                calls.add(child.func.attr)
        elif isinstance(child, ast.Name):
            names.add(child.id)
    
    return {
        'calls': list(calls)[:10],  # Limit to top 10
        'names': list(names)[:10]
    }


def extract_python_chunks(file_path: Path, workspace_root: Path) -> List[Document]:
    """
    Extract context-rich function and class level chunks from a Python file.
    
    Each chunk includes:
    - Module docstring and imports (for context)
    - The function/class definition
    - Metadata about what it references
    
    This creates separate documents for:
    - Each top-level function (with module context)
    - Each class with ALL its methods (with module context)
    - Module-level code (imports, constants, etc.)
    
    Args:
        file_path: Path to Python file
        workspace_root: Workspace root for relative paths
        
    Returns:
        List of Documents, one per function/class
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.split('\n')
        
        tree = ast.parse(content)
        rel_path = str(file_path.relative_to(workspace_root))
        documents = []
        
        # Extract module-level context (imports, docstrings, constants)
        module_context = extract_module_context(tree, lines)
        context_header = module_context['content']
        
        # Track what lines are covered by functions/classes
        covered_lines = set()
        processed_classes = set()
        
        # Extract top-level classes (with ALL methods) and functions
        for node in tree.body:  # Only look at top-level, not nested
            if isinstance(node, ast.ClassDef):
                # Process entire class (not individual methods)
                try:
                    start_line = node.lineno - 1
                    end_line = node.end_lineno
                    
                    # Get the complete class code
                    chunk_lines = lines[start_line:end_line]
                    chunk_content = '\n'.join(chunk_lines)
                    
                    # Prepend module context
                    if context_header:
                        full_content = f"{context_header}\n\n# --- Class Definition ---\n\n{chunk_content}"
                    else:
                        full_content = chunk_content
                    
                    # Mark these lines as covered
                    for line_num in range(start_line, end_line):
                        covered_lines.add(line_num)
                    
                    # Extract what this class references
                    references = extract_names_from_node(node)
                    
                    # Get method names
                    method_names = [m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    
                    # Build metadata
                    metadata = {
                        "path": rel_path,
                        "type": "py",
                        "chunk_type": "class",
                        "name": node.name,
                        "start_line": start_line + 1,
                        "end_line": end_line,
                        "methods": method_names[:20],  # List of method names
                        "imports": module_context['imports'][:10],
                        "calls": references['calls']
                    }
                    
                    # Add docstring to metadata if present
                    docstring = ast.get_docstring(node)
                    if docstring:
                        metadata["docstring"] = docstring[:200]
                    
                    # Create document
                    doc = Document(
                        page_content=full_content,
                        metadata=metadata
                    )
                    documents.append(doc)
                    processed_classes.add(node.name)
                    
                except Exception as e:
                    continue
            
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Process top-level functions
                try:
                    start_line = node.lineno - 1
                    end_line = node.end_lineno
                    
                    # Get the function code
                    chunk_lines = lines[start_line:end_line]
                    chunk_content = '\n'.join(chunk_lines)
                    
                    # Prepend module context
                    if context_header:
                        full_content = f"{context_header}\n\n# --- Function Definition ---\n\n{chunk_content}"
                    else:
                        full_content = chunk_content
                    
                    # Mark these lines as covered
                    for line_num in range(start_line, end_line):
                        covered_lines.add(line_num)
                    
                    # Extract what this function references
                    references = extract_names_from_node(node)
                    
                    # Get function arguments
                    args = [arg.arg for arg in node.args.args]
                    
                    # Build metadata
                    metadata = {
                        "path": rel_path,
                        "type": "py",
                        "chunk_type": "function",
                        "name": node.name,
                        "start_line": start_line + 1,
                        "end_line": end_line,
                        "args": args,
                        "imports": module_context['imports'][:10],
                        "calls": references['calls']
                    }
                    
                    # Add docstring to metadata if present
                    docstring = ast.get_docstring(node)
                    if docstring:
                        metadata["docstring"] = docstring[:200]
                    
                    # Create document
                    doc = Document(
                        page_content=full_content,
                        metadata=metadata
                    )
                    documents.append(doc)
                    
                except Exception as e:
                    continue
        
        # Extract module-level code (imports, constants, etc.) as a separate chunk
        module_lines = []
        for i, line in enumerate(lines):
            if i not in covered_lines and line.strip():
                module_lines.append(line)
        
        if module_lines:
            module_content = '\n'.join(module_lines)
            # Only include if substantial (not just imports)
            if len(module_content.strip()) > 50:
                metadata = {
                    "path": rel_path,
                    "type": "py",
                    "chunk_type": "module",
                    "name": "module_level",
                    "imports": module_context['imports'][:10]
                }
                
                # Add module docstring if present
                module_doc = ast.get_docstring(tree)
                if module_doc:
                    metadata["docstring"] = module_doc[:200]
                
                doc = Document(
                    page_content=module_content,
                    metadata=metadata
                )
                documents.append(doc)
        
        return documents if documents else []
        
    except Exception as e:
        # If chunking fails, return empty list (will fall back to whole file)
        return []


def file_to_documents(file_path: Path, workspace_root: Path) -> List[Document]:
    """
    Convert a file to one or more LangChain Documents.
    
    For Python files: Returns multiple documents (one per function/class)
    For other files: Returns a single document with full content

    Args:
        file_path: Absolute path to file
        workspace_root: Absolute path to workspace root

    Returns:
        List of Documents (multiple for Python files, single for others)
    """
    try:
        # For Python files, use function-level chunking
        if file_path.suffix == ".py":
            chunks = extract_python_chunks(file_path, workspace_root)
            if chunks:
                return chunks
            # If chunking fails, fall through to whole-file approach
        
        # For non-Python files or if chunking failed, use whole-file approach
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
            "size": len(content),
            "chunk_type": "full_file"
        }

        if summary:
            metadata["summary"] = summary

        doc = Document(
            page_content=content,
            metadata=metadata
        )

        return [doc]

    except Exception as e:
        return []


def index_codebase(workspace_root: str = ".") -> Dict[str, Any]:
    """
    Index entire codebase for semantic search.

    Walks through files, converts to Documents, and stores in Pinecone.
    Python files are chunked at function/class level for better semantic search.

    Args:
        workspace_root: Path to workspace root (default: current directory)

    Returns:
        Dict with indexing results

    Example:
        result = index_codebase(".")
        print(f"Indexed {result['total_chunks']} chunks from {result['total_files']} files")
    """
    workspace_path = Path(workspace_root).resolve()

    if not workspace_path.exists():
        return {
            "error": f"Workspace not found: {workspace_path}",
            "total_files": 0,
            "total_chunks": 0
        }

    # Collect all documents (can be multiple per file for Python files)
    documents = []
    files_processed = 0

    for file_path in workspace_path.rglob('*'):
        if not file_path.is_file():
            continue

        if not should_index_file(file_path):
            continue

        docs = file_to_documents(file_path, workspace_path)
        if docs:
            documents.extend(docs)
            files_processed += 1

    if not documents:
        return {
            "error": "No files found to index",
            "total_files": 0,
            "total_chunks": 0
        }

    try:
        # Get vector store
        vector_store = get_cached_vector_store(namespace="codebase")

        # Add all documents (LangChain handles embedding + storage)
        vector_store.add_documents(documents)

        return {
            'total_files': files_processed,
            'total_chunks': len(documents),
            'workspace': str(workspace_path)
        }

    except Exception as e:
        error_msg = f"Error indexing documents: {str(e)}"

        return {
            "error": error_msg,
            "total_files": 0,
            "total_chunks": 0
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
