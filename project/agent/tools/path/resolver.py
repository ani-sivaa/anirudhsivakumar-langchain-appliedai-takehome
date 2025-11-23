"""
Path Resolver with Fuzzy Matching

Helps correct typos in file paths by finding similar existing paths.
Uses Levenshtein distance for fuzzy matching.
"""

from pathlib import Path
from typing import Optional, List, Tuple
import difflib


def get_all_paths(root: str = ".") -> List[str]:
    """Get all file and directory paths in project."""
    root_path = Path(root).resolve()
    paths = []

    # Get all files and directories
    for path in root_path.rglob("*"):
        # Skip hidden and common ignored directories
        if any(part.startswith(".") for part in path.parts):
            continue
        if any(ignore in path.parts for ignore in ["node_modules", "__pycache__", "venv", ".venv"]):
            continue

        rel_path = str(path.relative_to(root_path))
        paths.append(rel_path)

    return paths


def find_similar_paths(target: str, threshold: float = 0.6) -> List[Tuple[str, float]]:
    """
    Find paths similar to the target using fuzzy matching.

    Args:
        target: The path with potential typo
        threshold: Minimum similarity score (0.0 to 1.0)

    Returns:
        List of (path, score) tuples sorted by similarity

    Example:
        find_similar_paths("protfolio/style.css")
        # Returns: [("portfolio/styles/style.css", 0.85), ...]
    """
    all_paths = get_all_paths()

    # Use difflib for fuzzy string matching
    matches = difflib.get_close_matches(
        target,
        all_paths,
        n=5,  # Return top 5 matches
        cutoff=threshold
    )

    # Calculate similarity scores
    results = []
    for match in matches:
        score = difflib.SequenceMatcher(None, target.lower(), match.lower()).ratio()
        results.append((match, score))

    return sorted(results, key=lambda x: x[1], reverse=True)


def resolve_path(path: str, auto_correct: bool = True) -> Tuple[str, Optional[str]]:
    """
    Resolve a path, correcting typos if needed.

    Args:
        path: Path that may contain typos
        auto_correct: If True, automatically use best match

    Returns:
        (resolved_path, suggestion_message)
        - If path exists: (original_path, None)
        - If path has typo and match found: (corrected_path, message)
        - If no match found: (original_path, None)

    Example:
        resolve_path("protfolio/style.css")
        # Returns: ("portfolio/styles/style.css",
        #           "Did you mean 'portfolio/styles/style.css'?")
    """
    path_obj = Path(path)

    # If path exists, return it
    if path_obj.exists():
        return (path, None)

    # Try to find similar paths
    similar = find_similar_paths(path, threshold=0.6)

    if not similar:
        return (path, None)

    best_match, score = similar[0]

    # If very confident (score > 0.75), auto-correct
    if auto_correct and score > 0.75:
        message = f"Note: Corrected '{path}' → '{best_match}' (typo detected)"
        return (best_match, message)

    # Otherwise, suggest
    if score > 0.6:
        message = f"File '{path}' not found. Did you mean '{best_match}'?"
        return (path, message)

    return (path, None)


def resolve_directory(path: str) -> Tuple[str, Optional[str]]:
    """
    Resolve a directory path, handling typos.

    Similar to resolve_path but specifically for directories.
    """
    all_paths = get_all_paths()
    directories = [p for p in all_paths if Path(p).is_dir()]

    # Check if directory exists
    if Path(path).is_dir():
        return (path, None)

    # Find similar directories
    matches = difflib.get_close_matches(path, directories, n=1, cutoff=0.6)

    if matches:
        best_match = matches[0]
        score = difflib.SequenceMatcher(None, path.lower(), best_match.lower()).ratio()

        if score > 0.75:
            message = f"Note: Corrected directory '{path}' → '{best_match}'"
            return (best_match, message)

    return (path, None)


def extract_directory_from_description(description: str) -> Optional[str]:
    """
    Extract directory name from natural language.

    Handles phrases like:
    - "look at the portfolio folder"
    - "edit files in the tests directory"
    - "check the agent/nodes directory"

    Returns:
        Directory name or None if not found
    """
    import re

    # Patterns to match
    patterns = [
        r"(?:in|at|the)\s+(?:the\s+)?([a-zA-Z0-9_/-]+)\s+(?:folder|directory|dir)",
        r"([a-zA-Z0-9_/-]+)/",  # Anything with a slash
    ]

    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            return match.group(1)

    return None

