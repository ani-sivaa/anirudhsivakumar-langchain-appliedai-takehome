import subprocess
import os
import re
from typing import Dict
from pathlib import Path

from agent.state import AgentState


def resolve_path_in_command(command: str) -> str:
    """
    Resolve paths in destructive commands by checking if they exist.
    If not found in cwd, search common locations (parent dir, etc).

    Args:
        command: The shell command to potentially fix

    Returns:
        Updated command with corrected paths, or original if no fix needed
    """
    # Only fix destructive commands that target paths
    destructive_patterns = [
        r'^rm\s+(-[rfv]+\s+)?(.+)$',  # rm, rm -rf, etc
        r'^rmdir\s+(.+)$',             # rmdir
    ]

    for pattern in destructive_patterns:
        match = re.match(pattern, command.strip())
        if match:
            # Extract the path (last group in the match)
            path_arg = match.groups()[-1]

            # Remove quotes if present
            path_arg_clean = path_arg.strip().strip('"').strip("'")

            # Handle wildcards by stripping them for existence check
            # but preserving them in the final path
            wildcard_suffix = ""
            base_path = path_arg_clean
            if path_arg_clean.endswith("/*"):
                wildcard_suffix = "/*"
                base_path = path_arg_clean[:-2]
            elif path_arg_clean.endswith("*"):
                wildcard_suffix = "*"
                base_path = path_arg_clean[:-1].rstrip("/")

            # Check if path exists as-is (without wildcard)
            if not os.path.exists(base_path):
                # Try common locations
                candidates = [
                    ("../" + base_path, "../" + path_arg_clean),  # Parent directory
                    ("./" + base_path, "./" + path_arg_clean),    # Explicit current dir
                ]

                for base_candidate, full_candidate in candidates:
                    if os.path.exists(base_candidate):
                        # Found it! Update the command
                        # Preserve quotes if original had them or if path has spaces
                        if '"' in path_arg or "'" in path_arg or ' ' in full_candidate:
                            fixed_path = f'"{full_candidate}"'
                        else:
                            fixed_path = full_candidate

                        # Replace the original path with the fixed one
                        fixed_command = command.replace(path_arg, fixed_path)
                        return fixed_command

            # Path exists as-is or we couldn't find it - return original
            return command

    # Not a destructive command or no match - return original
    return command


def run_shell(state: AgentState) -> Dict:
    """
    Runs shell commands like ls, git status, etc.
    Has a 30 second timeout so it doesn't hang forever.
    Dangerous commands get caught by the approval workflow before this runs.
    """
    command = state.get("command", "")

    if not command:
        return {"error": "No command provided"}

    # Try to resolve paths in destructive commands
    original_command = command
    command = resolve_path_in_command(command)

    # If command was fixed, add a note
    command_note = ""
    if command != original_command:
        command_note = f"(Path resolved: {original_command} → {command})\n"

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout if result.stdout else result.stderr

        # Always show the command that was executed
        response_text = ""
        if command_note:
            response_text += command_note
        response_text += f"Command executed (exit code {result.returncode}):\n$ {command}"
        if output:
            response_text += f"\n{output}"

        return {
            "shell_output": output,
            "return_code": result.returncode,
            "response": response_text,
            "messages": [{"role": "assistant", "content": f"Ran: {command}\n{output}"}],
            "error": ""
        }
        
    except subprocess.TimeoutExpired:
        return {
            "error": f"Command timed out after 30 seconds: {command}\n"
                     "The command might be waiting for input or taking too long to complete.",
            "shell_output": "TIMEOUT",
            "return_code": -1,
            "response": f"Command '{command}' timed out after 30 seconds",
            "messages": [{"role": "assistant", "content": f"Command '{command}' timed out"}]
        }
    except Exception as e:
        return {"error": f"Error running command: {str(e)}"}

