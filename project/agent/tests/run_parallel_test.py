#!/usr/bin/env python3
"""
Test to verify parallel execution of LLM calls in LangGraph.
"""

import asyncio
import sys
import re
from datetime import datetime
from agent.graph import get_agent_graph


class LogCapture:
    """Capture print statements to analyze timing."""
    
    def __init__(self):
        self.logs = []
        self.original_print = print
    
    def __enter__(self):
        def custom_print(*args, **kwargs):
            msg = ' '.join(str(arg) for arg in args)
            if '[PARALLEL]' in msg:
                self.logs.append(msg)
            self.original_print(*args, **kwargs)
        
        import builtins
        builtins.print = custom_print
        return self
    
    def __exit__(self, *args):
        import builtins
        builtins.print = self.original_print


def parse_parallel_logs(logs):
    """Parse [PARALLEL] log lines to extract timing information."""
    starts = {}
    results = []
    
    for log in logs:
        if '[PARALLEL] Starting:' in log:
            match = re.search(r'Starting: (.+?) @ ([\d:\.]+)', log)
            if match:
                file_path = match.group(1)
                time_str = match.group(2)
                try:
                    start_time = datetime.strptime(time_str, "%H:%M:%S.%f")
                except ValueError:
                    try:
                        start_time = datetime.strptime(time_str, "%H:%M:%S")
                    except ValueError:
                        continue
                starts[file_path] = start_time
        
        elif '[PARALLEL] Completed:' in log:
            match = re.search(r'Completed: (.+?) @', log)
            if match:
                file_path = match.group(1)
                start_time = starts.get(file_path)
                
                if start_time:
                    llm_match = re.search(r'LLM: ([\d\.]+)s', log)
                    total_match = re.search(r'Total: ([\d\.]+)s', log)
                    
                    if llm_match and total_match:
                        llm_time = float(llm_match.group(1))
                        total_time = float(total_match.group(1))
                        results.append((file_path, start_time, llm_time, total_time))
                        starts.pop(file_path, None)
    
    return results


def analyze_parallelism(results):
    """Analyze if calls were parallel based on timing."""
    if len(results) < 2:
        print("\nError: Need at least 2 calls to analyze parallelism")
        return False
    
    print("\n" + "=" * 80)
    print("PARALLEL EXECUTION ANALYSIS")
    print("=" * 80)
    print()
    
    results.sort(key=lambda x: x[1])
    
    print("Call Timeline:")
    print("-" * 80)
    for i, (file_path, start_time, llm_time, total_time) in enumerate(results, 1):
        short_path = file_path.split('/')[-1] if '/' in file_path else file_path
        print(f"{i}. {short_path}")
        print(f"   Start: {start_time.strftime('%H:%M:%S.%f')[:-3]}")
        print(f"   LLM call: {llm_time:.2f}s")
        print(f"   Total: {total_time:.2f}s")
        print()
    
    first_start = results[0][1]
    last_start = results[-1][1]
    start_diff = (last_start - first_start).total_seconds()
    
    max_llm_time = max(r[2] for r in results)
    sum_llm_time = sum(r[2] for r in results)
    
    earliest_start = min(r[1] for r in results)
    latest_end_times = [(r[1].timestamp() + r[3]) for r in results]
    latest_end = max(latest_end_times)
    total_wall_time = latest_end - earliest_start.timestamp()
    
    print("Analysis:")
    print("-" * 80)
    print(f"Start time spread: {start_diff:.3f}s")
    print(f"Longest LLM call: {max_llm_time:.2f}s")
    print(f"Sum of all LLM calls: {sum_llm_time:.2f}s")
    print(f"Total wall-clock time: {total_wall_time:.2f}s")
    print()
    
    is_parallel = True
    checks = []
    
    if start_diff < 0.1:
        checks.append(("PASS", "All calls started nearly simultaneously"))
    else:
        checks.append(("FAIL", f"Calls started {start_diff:.3f}s apart (sequential)"))
        is_parallel = False
    
    if total_wall_time < sum_llm_time * 0.8:
        checks.append(("PASS", f"Total time ({total_wall_time:.2f}s) is much less than sum ({sum_llm_time:.2f}s)"))
    else:
        checks.append(("FAIL", f"Total time ({total_wall_time:.2f}s) is close to sum ({sum_llm_time:.2f}s)"))
        is_parallel = False
    
    if total_wall_time <= max_llm_time * 1.3:
        checks.append(("PASS", f"Total time ({total_wall_time:.2f}s) is close to longest call ({max_llm_time:.2f}s)"))
    else:
        checks.append(("WARN", f"Total time ({total_wall_time:.2f}s) is longer than longest call ({max_llm_time:.2f}s)"))
    
    for check, msg in checks:
        print(f"[{check}] {msg}")
    
    print()
    print("=" * 80)
    print()
    
    if is_parallel:
        print("RESULT: Calls executed in parallel")
        print(f"  {len(results)} calls executed concurrently")
        print(f"  Time saved: {sum_llm_time - total_wall_time:.2f}s (vs sequential)")
    else:
        print("RESULT: Calls executed sequentially")
        print("  Calls may be blocking each other")
    
    print()
    return is_parallel


async def main():
    print("=" * 80)
    print("PARALLEL EXECUTION VERIFICATION TEST")
    print("=" * 80)
    print()
    print("Creating 3 test files to verify parallel LLM execution...")
    print()
    
    agent_graph = await get_agent_graph()
    config = {
        "configurable": {
            "thread_id": f"test_parallel_{int(asyncio.get_event_loop().time())}",
            "max_concurrency": 50
        }
    }
    
    user_input = "Create 3 test files: test1.py with a hello function, test2.py with a goodbye function, test3.py with a main function"
    
    with LogCapture() as log_capture:
        async for event in agent_graph.astream(
            {"user_input": user_input},
            config=config,
            stream_mode="updates"
        ):
            pass
    
    results = parse_parallel_logs(log_capture.logs)
    
    if results:
        is_parallel = analyze_parallelism(results)
        sys.exit(0 if is_parallel else 1)
    else:
        print("\nError: No [PARALLEL] log entries found.")
        print("Make sure the operation triggered parallel file creation.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
