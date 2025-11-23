import subprocess
from typing import Dict

from agent.state import AgentState


def run_shell(state: AgentState) -> Dict:
    """
    Runs shell commands like ls, git status, etc.
    Has a 30 second timeout so it doesn't hang forever.
    Dangerous commands get caught by the approval workflow before this runs.
    """
    command = state.get("command", "")
    
    if not command:
        return {"error": "No command provided"}
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout if result.stdout else result.stderr
        
        return {
            "shell_output": output,
            "return_code": result.returncode,
            "response": f"Command executed (exit code {result.returncode}):\n{output}",
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

