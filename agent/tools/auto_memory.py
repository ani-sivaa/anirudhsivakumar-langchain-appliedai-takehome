"""
Auto-memory utilities - automatically capture and update long-term project context.
Keeps the agent smart about the project structure and important context.
"""

import os
from pathlib import Path
from typing import Dict, List
from datetime import datetime


def get_project_structure(max_depth: int = 3) -> Dict[str, any]:
    """
    Scans the current project and returns a structured summary.
    Skips common ignore patterns (node_modules, .git, __pycache__, etc.)
    """
    workspace = Path.cwd()
    ignore_patterns = {
        '.git', '__pycache__', '.pytest_cache', '.venv', 'venv',
        'node_modules', '.env', '*.pyc', '.DS_Store', 'data', '*.db',
        '*.sqlite', '*.sqlite3', 'dry_run_test', 'test_dir', 'GOAT'
    }
    
    structure = {
        'root': str(workspace),
        'scanned_at': datetime.now().isoformat(),
        'directories': {},
        'important_files': []
    }
    
    def should_ignore(path: Path) -> bool:
        """Check if path matches ignore patterns"""
        parts = path.relative_to(workspace).parts
        return any(
            pattern.strip('*') in str(path).lower() 
            for pattern in ignore_patterns
        )
    
    def scan_dir(path: Path, depth: int = 0):
        """Recursively scan directory"""
        if depth > max_depth:
            return []
        
        items = []
        try:
            for item in sorted(path.iterdir()):
                if should_ignore(item):
                    continue
                
                rel_path = str(item.relative_to(workspace))
                
                if item.is_file():
                    # Track important file types
                    if item.suffix in ['.py', '.md', '.txt', '.json', '.yaml', '.yml', '.toml']:
                        items.append({
                            'path': rel_path,
                            'type': 'file',
                            'extension': item.suffix,
                            'size': item.stat().st_size
                        })
                elif item.is_dir():
                    sub_items = scan_dir(item, depth + 1)
                    if sub_items:  # Only include non-empty dirs
                        items.append({
                            'path': rel_path,
                            'type': 'directory',
                            'contents': sub_items
                        })
        except PermissionError:
            pass
        
        return items
    
    structure['directories'] = scan_dir(workspace)
    return structure


def extract_file_list(structure: Dict) -> List[str]:
    """
    Flattens the project structure into a simple list of file paths.
    Useful for quick lookups.
    """
    files = []
    
    def traverse(items):
        for item in items:
            if item['type'] == 'file':
                files.append(item['path'])
            elif item['type'] == 'directory':
                traverse(item.get('contents', []))
    
    traverse(structure.get('directories', []))
    return files


def identify_project_type(structure: Dict) -> str:
    """
    Infers what kind of project this is based on files present.
    """
    files = extract_file_list(structure)
    file_set = set(files)
    
    # Check for common project markers
    if 'requirements.txt' in file_set or 'setup.py' in file_set:
        if any('agent/' in f for f in files):
            return 'LangGraph Agent Project'
        return 'Python Project'
    
    if 'package.json' in file_set:
        return 'Node.js Project'
    
    if 'Cargo.toml' in file_set:
        return 'Rust Project'
    
    if 'go.mod' in file_set:
        return 'Go Project'
    
    return 'Unknown Project'


def get_key_files(structure: Dict) -> List[str]:
    """
    Identifies the most important files in the project.
    These are typically entry points, configs, and documentation.
    """
    files = extract_file_list(structure)
    
    # Priority files to remember
    priority_patterns = [
        'README.md',
        'main.py',
        'app.py',
        'graph.py',
        'state.py',
        'requirements.txt',
        'package.json',
        '.env.example',
        'config',
        'settings'
    ]
    
    key_files = []
    for pattern in priority_patterns:
        matches = [f for f in files if pattern.lower() in f.lower()]
        key_files.extend(matches)
    
    return list(set(key_files))  # Deduplicate


def build_project_memory(user_id: str = "default_user") -> Dict:
    """
    Builds a complete memory entry for the current project state.
    This is what gets stored in long-term memory.
    """
    structure = get_project_structure()
    
    return {
        'user_id': user_id,
        'namespace': ['project', 'structure'],
        'memory': {
            'project_root': structure['root'],
            'project_type': identify_project_type(structure),
            'key_files': get_key_files(structure),
            'all_files': extract_file_list(structure),
            'last_updated': structure['scanned_at'],
            'file_count': len(extract_file_list(structure))
        }
    }


def should_auto_update_memory(action: str) -> bool:
    """
    Determines if we should automatically update project memory after this action.
    """
    auto_update_actions = {'edit', 'edit_multi', 'project'}
    return action in auto_update_actions

