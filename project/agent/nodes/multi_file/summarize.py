from typing import Dict
from pathlib import Path
from datetime import datetime

from agent.state import AgentState


def summarize_multi_edit(state: AgentState) -> Dict:
    """
    After editing multiple files in parallel, this counts up the successes and failures.
    Shows which files worked and which didn't.
    """
    edit_results = state.get("edit_results", [])
    paths = state.get("paths", [])
    user_input = state.get("user_input", "")
    edit_start_time = state.get("edit_start_time", 0)
    edit_file_timings = state.get("edit_file_timings", {})

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
                # Show both filename and error reason for better debugging
                parts = result.replace("FAIL: ", "").split(" - ", 1)
                file_path = parts[0]
                error_reason = parts[1] if len(parts) > 1 else "Unknown error"
                summary_lines.append(f"  - {Path(file_path).name}: {error_reason}")
        error_msg = "Some files failed to update"
    else:
        error_msg = ""

    # Calculate parallel performance gains
    if edit_start_time and edit_file_timings:
        wall_clock_time = datetime.now().timestamp() - edit_start_time
        sequential_time = sum(edit_file_timings.values())

        if sequential_time > 0 and wall_clock_time > 0:
            time_saved = sequential_time - wall_clock_time
            speedup_factor = sequential_time / wall_clock_time

            summary_lines.append(f"\n⚡ Parallel Performance:")
            summary_lines.append(f"  Sequential time: {sequential_time:.2f}s")
            summary_lines.append(f"  Parallel time: {wall_clock_time:.2f}s")
            summary_lines.append(f"  Time saved: {time_saved:.2f}s ({speedup_factor:.1f}x speedup)")

    summary = "\n".join(summary_lines)

    return {
        "response": summary,
        "error": error_msg,
        "messages": [
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": summary}
        ]
    }

