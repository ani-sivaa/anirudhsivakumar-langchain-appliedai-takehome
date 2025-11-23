from typing import Dict
from pathlib import Path

from agent.state import AgentState


def summarize_multi_edit(state: AgentState) -> Dict:
    """
    After editing multiple files in parallel, this counts up the successes and failures.
    Shows which files worked and which didn't.
    """
    edit_results = state.get("edit_results", [])
    paths = state.get("paths", [])
    user_input = state.get("user_input", "")
    
    if not edit_results:
        return {
            "response": "Multi-file edit completed, but no results were recorded.",
            "error": "",
            "messages": [
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": "Multi-file edit completed"}
            ]
        }
    
    success_count = sum(1 for r in edit_results if r.startswith("SUCCESS:"))
    failure_count = sum(1 for r in edit_results if r.startswith("FAIL:"))
    
    # Build cleaner summary
    summary_lines = [f"Multi-file edit complete: {success_count} file(s) updated"]
    
    if success_count > 0:
        summary_lines.append("\nUpdated files:")
        for result in edit_results:
            if result.startswith("SUCCESS:"):
                # Extract just the filename or relative path
                file_path = result.replace("SUCCESS: ", "").strip()
                try:
                    # Try to show relative path
                    rel_path = Path(file_path).relative_to(Path.cwd())
                    summary_lines.append(f"  - {rel_path}")
                except (ValueError, TypeError):
                    # Fall back to just filename
                    summary_lines.append(f"  - {Path(file_path).name}")
    
    if failure_count > 0:
        summary_lines.append(f"\n{failure_count} file(s) failed:")
        for result in edit_results:
            if result.startswith("FAIL:"):
                file_path = result.replace("FAIL: ", "").split(" - ")[0]
                summary_lines.append(f"  - {Path(file_path).name}")
        error_msg = "Some files failed to update"
    else:
        error_msg = ""
    
    summary = "\n".join(summary_lines)
    
    return {
        "response": summary,
        "error": error_msg,
        "messages": [
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": summary}
        ]
    }

