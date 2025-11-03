from typing import Dict

from agent.state import AgentState


def summarize_multi_edit(state: AgentState) -> Dict:
    """
    After editing multiple files in parallel, this counts up the successes and failures.
    Shows which files worked and which didn't.
    """
    edit_results = state.get("edit_results", [])
    paths = state.get("paths", [])
    
    if not edit_results:
        return {
            "response": "Multi-file edit completed, but no results were recorded.",
            "error": "",
            "messages": [{"role": "assistant", "content": "Multi-file edit completed"}]
        }
    
    success_count = sum(1 for r in edit_results if r.startswith("SUCCESS:"))
    failure_count = sum(1 for r in edit_results if r.startswith("✗"))
    
    summary_lines = [f"Multi-file edit complete: {len(paths)} file(s) processed"]
    summary_lines.append("")
    
    for result in edit_results:
        summary_lines.append(result)
    
    if failure_count > 0:
        summary_lines.append(f"\nResults: {success_count} succeeded, {failure_count} failed")
        error_msg = "Some files failed to update"
    else:
        summary_lines.append(f"\nAll {success_count} files updated successfully")
        error_msg = ""
    
    summary = "\n".join(summary_lines)
    
    return {
        "response": summary,
        "error": error_msg,
        "messages": [{"role": "assistant", "content": summary}]
    }

