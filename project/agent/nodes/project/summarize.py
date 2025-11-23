import time
from typing import Dict

from agent.state import AgentState


def summarize_project(state: AgentState) -> Dict:
    """
    Summarize project creation results.
    """
    project_results = state.get("project_results", [])
    user_input = state.get("user_input", "")
    project_file_timings = state.get("project_file_timings", {})
    project_start_time = state.get("project_start_time")

    success_files = [r for r in project_results if r.startswith("SUCCESS:")]
    failed_files = [r for r in project_results if r.startswith("FAIL:")]

    if not success_files and not failed_files:
        return {
            "response": "No files were created",
            "error": "Project creation failed"
        }

    # Calculate timing statistics
    timing_lines = []
    if project_file_timings:
        # Calculate total parallel time (max of individual times - since they run in parallel)
        # This represents the actual wall-clock time for parallel execution
        total_parallel_time = max(project_file_timings.values()) if project_file_timings else 0

        # Calculate sequential time (sum of all individual file times)
        # This is what it would take if files were created one after another
        sequential_time = sum(project_file_timings.values())

        # Calculate saved time
        saved_time = sequential_time - total_parallel_time

        if saved_time > 0 and sequential_time > 0:
            speedup_factor = sequential_time / total_parallel_time
            timing_lines.append(f"\n⚡ Parallel Performance:")
            timing_lines.append(f"  Sequential time: {sequential_time:.2f}s")
            timing_lines.append(f"  Parallel time: {total_parallel_time:.2f}s")
            timing_lines.append(f"  Time saved: {saved_time:.2f}s ({speedup_factor:.1f}x speedup)")

    # Build summary
    summary_lines = []
    if success_files:
        summary_lines.append(f"Project complete! Created {len(success_files)} file(s):")
        summary_lines.extend(success_files)

    if failed_files:
        summary_lines.append(f"\n{len(failed_files)} file(s) failed:")
        summary_lines.extend(failed_files)

    # Add timing information
    summary_lines.extend(timing_lines)

    summary = "\n".join(summary_lines)

    return {
        "response": summary,
        "messages": [
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": summary}
        ],
        "error": "Some files failed" if failed_files else ""
    }

