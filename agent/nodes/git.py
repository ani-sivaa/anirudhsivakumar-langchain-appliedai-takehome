import subprocess
from typing import Dict

from agent.state import AgentState


def get_git_diff(state: AgentState) -> Dict:
    """
    Gets git diffs between two branches for PR review.
    First finds all changed files, then gets the diff for each one.
    """
    base_branch = state.get("base_branch", "main")
    head_branch = state.get("head_branch", "HEAD")
    
    try:
        files_result = subprocess.run(
            ["git", "diff", "--name-only", f"{base_branch}..{head_branch}"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if files_result.returncode != 0:
            return {"error": f"Failed to get changed files: {files_result.stderr}"}
        
        changed_files = [f.strip() for f in files_result.stdout.strip().split("\n") if f.strip()]
        
        if not changed_files:
            return {
                "error": "",
                "diffs": [],
                "messages": [{"role": "assistant", "content": f"No changes between {base_branch} and {head_branch}"}]
            }
        
        diffs = []
        for file_path in changed_files:
            diff_result = subprocess.run(
                ["git", "diff", f"{base_branch}..{head_branch}", "--", file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if diff_result.returncode == 0:
                diffs.append({"file": file_path, "diff": diff_result.stdout})
        
        return {"diffs": diffs, "error": ""}
        
    except subprocess.TimeoutExpired:
        return {"error": "Git diff timed out"}
    except Exception as e:
        return {"error": f"Error getting git diff: {str(e)}"}

