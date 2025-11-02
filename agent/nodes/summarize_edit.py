from typing import Dict

from agent.state import AgentState


def summarize_multi_edit(state: AgentState) -> Dict:
    edit_results = state.get("edit_results", [])
    paths = state.get("paths", [])
    
    if not edit_results:
        return {
            "response": "Multi-file edit completed, but no results were recorded.",
            "error": "",
            "messages": [{"role": "assistant", "content": "Multi-file edit completed"}]
        }
    
    success_count = sum(1 for r in edit_results if r.startswith("✓"))
    failure_count = sum(1 for r in edit_results if r.startswith("✗"))
    
    summary_lines = [f"Edited {len(paths)} file(s):"]
    for result in edit_results:
        summary_lines.append(result)
    
    if failure_count > 0:
        summary_lines.append(f"\n{success_count} succeeded, {failure_count} failed")
    
    summary = "\n".join(summary_lines)
    
    return {
        "response": summary,
        "error": "",
        "messages": [{"role": "assistant", "content": summary}]
    }

