"""
Codebase indexing - scans and stores code content in long-term memory.
This allows the agent to search and understand the codebase.
"""

from pathlib import Path
from typing import List, Dict
from datetime import datetime


def should_index_file(file_path: Path) -> bool:
    """Determine if a file should be indexed."""
    # Index these file types
    index_extensions = {'.py', '.md', '.txt', '.json', '.yaml', '.yml', '.toml', '.js', '.ts', '.tsx', '.jsx'}
    
    # Skip these patterns
    skip_patterns = [
        '__pycache__', '.pytest_cache', '.venv', 'venv', 'node_modules',
        '.git', '.env', 'data/', '*.pyc', '.DS_Store', '*.db', '*.sqlite',
        'dry_run_test', 'test_dir', 'GOAT', 'website'
    ]
    
    file_str = str(file_path)
    
    # Check skip patterns
    for pattern in skip_patterns:
        if pattern in file_str:
            return False
    
    # Check extension
    return file_path.suffix in index_extensions


def extract_code_summary(content: str, file_path: str) -> str:
    """Extract a summary of the code file."""
    lines = content.split('\n')
    
    summary_parts = []
    
    # For Python files, extract key info
    if file_path.endswith('.py'):
        # Get imports
        imports = [line.strip() for line in lines if line.strip().startswith(('import ', 'from '))]
        if imports:
            summary_parts.append(f"Imports: {', '.join(imports[:5])}")
        
        # Get function/class definitions
        definitions = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('def ') or stripped.startswith('class '):
                definitions.append(stripped.split('(')[0].split(':')[0])
        
        if definitions:
            summary_parts.append(f"Defines: {', '.join(definitions[:10])}")
    
    # For README/MD files, get first few lines
    elif file_path.endswith('.md'):
        non_empty = [line for line in lines[:10] if line.strip()]
        summary_parts.append(' '.join(non_empty[:3]))
    
    return ' | '.join(summary_parts) if summary_parts else content[:200]


def index_codebase(workspace_root: Path = None) -> Dict:
    """
    Index the entire codebase into a structured format.
    Returns indexed files ready to be stored in long-term memory.
    """
    if workspace_root is None:
        workspace_root = Path.cwd()
    
    indexed_files = []
    total_size = 0
    
    for file_path in workspace_root.rglob('*'):
        if not file_path.is_file():
            continue
        
        if not should_index_file(file_path):
            continue
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            rel_path = str(file_path.relative_to(workspace_root))
            
            # Create index entry
            entry = {
                'path': rel_path,
                'extension': file_path.suffix,
                'size': len(content),
                'lines': len(content.split('\n')),
                'content': content[:5000],  # Store first 5000 chars
                'summary': extract_code_summary(content, rel_path),
                'indexed_at': datetime.now().isoformat()
            }
            
            indexed_files.append(entry)
            total_size += len(content)
            
        except Exception as e:
            # Skip files we can't read
            continue
    
    return {
        'files': indexed_files,
        'total_files': len(indexed_files),
        'total_size': total_size,
        'indexed_at': datetime.now().isoformat(),
        'workspace': str(workspace_root)
    }


def store_codebase_index(store, index_data: Dict, user_id: str = "default_user"):
    """Store indexed codebase in long-term memory."""
    
    # Store overall index metadata
    store.put(
        namespace=("codebase", "index"),
        key="metadata",
        value={
            'total_files': index_data['total_files'],
            'total_size': index_data['total_size'],
            'indexed_at': index_data['indexed_at'],
            'workspace': index_data['workspace']
        }
    )
    
    # Store each file individually for searchability
    for file_entry in index_data['files']:
        store.put(
            namespace=("codebase", "files"),
            key=file_entry['path'],
            value=file_entry
        )


def search_codebase(store, query: str) -> List[Dict]:
    """Search indexed codebase for files matching query."""
    
    # Get all indexed files
    files = list(store.search(("codebase", "files")))
    
    matching_files = []
    query_lower = query.lower()
    
    for item in files:
        file_data = item.value if hasattr(item, 'value') else item
        
        # Search in path, summary, and content
        searchable = f"{file_data.get('path', '')} {file_data.get('summary', '')} {file_data.get('content', '')}"
        
        if query_lower in searchable.lower():
            matching_files.append(file_data)
    
    return matching_files[:20]  # Return top 20 matches

