import os
from pathlib import Path
from typing import Dict

from agent.state import AgentState


def edit_multi_passthrough(state: AgentState) -> Dict:
    """
    Passthrough node for multi-file editing - just returns empty dict.
    The actual work happens in the fan-out nodes.
    State already has paths and edit_instruction from determine_intent.
    If folder_path is provided, discovers files in that folder.
    """
    paths = state.get("paths", [])
    folder_path = state.get("folder_path", "")
    edit_instruction = state.get("edit_instruction", "")
    
    # If no paths but folder_path is provided, discover files in that folder
    if not paths and folder_path:
        try:
            folder = Path(folder_path).resolve()
            if not folder.exists():
                return {
                    "error": f"Folder not found: {folder_path}",
                    "response": f"I couldn't find the folder '{folder_path}'. Please check the path."
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
                    # Get relative path from folder
                    rel_path = file_path.relative_to(folder)
                    discovered_files.append(str(rel_path))
            
            if not discovered_files:
                return {
                    "error": f"No files found in folder: {folder_path}",
                    "response": f"I couldn't find any files in '{folder_path}'."
                }
            
            # Convert to absolute paths for consistency
            paths = [str(folder / f) for f in discovered_files]
            
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
    
    return {"paths": paths, "error": ""}

