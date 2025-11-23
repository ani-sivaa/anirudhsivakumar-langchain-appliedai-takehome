import os
from pathlib import Path
from typing import Dict

from agent.state import AgentState
from agent.nodes.file_ops.read import WORKSPACE_ROOT, AGENT_GENERATED_CODE_FOLDER


def edit_multi_passthrough(state: AgentState) -> Dict:
    """
    Passthrough node for multi-file editing - just returns empty dict.
    The actual work happens in the fan-out nodes.
    State already has paths and edit_instruction from determine_intent.
    If folder_path is provided, discovers files in that folder.
    
    IMPORTANT: Clears accumulated fields from previous runs to ensure clean state.
    """
    paths = state.get("paths", [])
    folder_path = state.get("folder_path", "")
    edit_instruction = state.get("edit_instruction", "")
    
    # If no paths but folder_path is provided, discover files in that folder
    if not paths and folder_path:
        try:
            # Normalize folder path - handle both relative and absolute paths
            # If path doesn't start with agent-generated-code, prepend it
            normalized_folder = folder_path.lstrip('/').lstrip('./')
            
            # Remove agent-generated-code prefix if already present (avoid duplication)
            if normalized_folder.startswith("agent-generated-code/"):
                normalized_folder = normalized_folder[len("agent-generated-code/"):]
            
            # Always look within agent-generated-code folder
            final_folder_path = f"agent-generated-code/{normalized_folder}"
            
            # Resolve to absolute path
            if Path(final_folder_path).is_absolute():
                folder = Path(final_folder_path)
            else:
                folder = WORKSPACE_ROOT / final_folder_path
            
            folder = folder.resolve()
            
            if not folder.exists():
                # Try without agent-generated-code prefix in case user provided absolute path
                alt_folder = Path(folder_path).resolve()
                if alt_folder.exists() and alt_folder.is_dir():
                    # Check if it's within agent-generated-code
                    try:
                        alt_folder.relative_to(AGENT_GENERATED_CODE_FOLDER)
                        folder = alt_folder
                    except ValueError:
                        # Not in agent-generated-code, use the normalized path
                        return {
                            "error": f"Folder not found: {folder_path}",
                            "response": f"I couldn't find the folder '{folder_path}'. Please check the path. Folders must be within agent-generated-code/."
                        }
                else:
                    return {
                        "error": f"Folder not found: {folder_path}",
                        "response": f"I couldn't find the folder '{folder_path}'. Please check the path. Folders must be within agent-generated-code/."
                    }
            
            if not folder.is_dir():
                return {
                    "error": f"Not a directory: {folder_path}",
                    "response": f"'{folder_path}' is not a directory."
                }
            
            # Find all files in the folder (excluding hidden files and common ignore patterns)
            discovered_files = []
            for root, dirs, files in os.walk(folder):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file in files:
                    if file.startswith('.'):
                        continue
                    file_path = Path(root) / file
                    # Get relative path from workspace root for consistency
                    try:
                        rel_path = file_path.relative_to(WORKSPACE_ROOT)
                        discovered_files.append(str(rel_path))
                    except ValueError:
                        # If not relative to workspace, get relative to folder and prepend agent-generated-code
                        rel_to_folder = file_path.relative_to(folder)
                        # Reconstruct the path relative to workspace
                        folder_rel = folder.relative_to(WORKSPACE_ROOT)
                        full_rel = folder_rel / rel_to_folder
                        discovered_files.append(str(full_rel))
            
            if not discovered_files:
                return {
                    "error": f"No files found in folder: {folder_path}",
                    "response": f"I couldn't find any files in '{folder_path}'."
                }
            
            # Use relative paths (they'll be normalized in read_file_multi)
            paths = discovered_files
            
        except Exception as e:
            return {
                "error": f"Error discovering files in folder: {str(e)}",
                "response": f"I encountered an error while looking for files in '{folder_path}': {str(e)}"
            }
    
    if not paths:
        return {
            "error": "No file paths specified for multi-file edit. Please specify which files to edit.",
            "response": "I need to know which files to edit. Can you specify the file paths or a folder path?"
        }
    
    if not edit_instruction:
        return {
            "error": "No edit instruction provided",
            "response": "What changes would you like me to make to these files?"
        }
    
    # Deduplicate paths to prevent processing the same file multiple times
    # This can happen if paths accumulate across runs
    unique_paths = []
    seen = set()
    for path in paths:
        # Normalize path for comparison
        normalized = str(Path(path).resolve()) if Path(path).exists() else path
        if normalized not in seen:
            seen.add(normalized)
            unique_paths.append(path)
    
    # Clear accumulated fields from previous runs to ensure clean state
    # This prevents failures from accumulating when user retries
    return {
        "paths": unique_paths,
        "error": "",
        "contents": {},  # Clear previous reads
        "modifications": {},  # Clear previous modifications
        "edit_results": ["__CLEAR__"]  # Clear previous results using special marker
    }

