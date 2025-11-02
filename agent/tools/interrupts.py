import re
from typing import Dict, Any


def is_dangerous_command(command: str) -> bool:
    dangerous_patterns = [
        r'\brm\b.*-rf',
        r'\brm\b.*-fr',
        r'\bdd\b',
        r'\bmkfs\b',
        r'>\s*/dev/',
        r'\bcurl\b.*\|\s*sh',
        r'\bwget\b.*\|\s*sh',
        r'\bsudo\b',
        r'\bchown\b.*-R',
        r'\bchmod\b.*-R',
        r'\bgit\b.*push.*--force',
        r'\bgit\b.*reset.*--hard',
        r'\bdocker\b.*rm',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    
    return False


def is_sensitive_file(path: str) -> bool:
    sensitive_patterns = [
        r'\.env',
        r'\.config',
        r'secrets',
        r'credentials',
        r'password',
        r'\.ssh/',
        r'\.aws/',
        r'package\.json',
        r'requirements\.txt',
    ]
    
    for pattern in sensitive_patterns:
        if re.search(pattern, path, re.IGNORECASE):
            return True
    
    return False


def format_file_diff(original: str, modified: str, path: str) -> str:
    import difflib
    
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
        lineterm=""
    )
    
    return "".join(list(diff))

