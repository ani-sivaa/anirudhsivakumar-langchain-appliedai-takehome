from typing import Dict

from agent.state import AgentState


def summarize_project(state: AgentState) -> Dict:
    """
    Summarize project creation results.
    """
    project_results = state.get("project_results", [])
    user_input = state.get("user_input", "")

    success_files = [r for r in project_results if r.startswith("SUCCESS:")]
    failed_files = [r for r in project_results if r.startswith("FAIL:")]

    if not success_files and not failed_files:
        return {
            "response": "No files were created",
            "error": "Project creation failed"
        }

    # Build summary
    summary_lines = []
    if success_files:
        summary_lines.append(f"Project complete! Created {len(success_files)} file(s):")
        summary_lines.extend(success_files)

    if failed_files:
        summary_lines.append(f"\n{len(failed_files)} file(s) failed:")
        summary_lines.extend(failed_files)

    summary = "\n".join(summary_lines)

    return {
        "response": summary,
        "messages": [
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": summary}
        ],
        "error": "Some files failed" if failed_files else ""
    }

