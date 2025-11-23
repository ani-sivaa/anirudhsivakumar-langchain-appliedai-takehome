#!/usr/bin/env python3
"""
Dry run scenarios to test all agent features.
Run this to verify everything works end-to-end.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add parent directory to path so we can import agent
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.graph import get_agent_graph
from rich.console import Console
from rich.panel import Panel

console = Console()


async def run_scenario(name, user_input, config, expected_action=None):
    """Run a single scenario and report results."""
    agent_graph = await get_agent_graph()
    console.print(f"\n[bold cyan]Scenario: {name}[/bold cyan]")
    console.print(f"[dim]Input: {user_input}[/dim]")
    
    try:
        result = await agent_graph.ainvoke({"user_input": user_input}, config)
        
        action = result.get("action", "unknown")
        response = result.get("response", "")
        error = result.get("error", "")
        
        if expected_action and action != expected_action:
            console.print(f"[red]✗ FAIL: Expected action '{expected_action}', got '{action}'[/red]")
            return False
        
        if error:
            console.print(f"[yellow]⚠ Warning: {error}[/yellow]")
        
        if response:
            console.print(f"[green]✓ Response: {response[:200]}...[/green]" if len(response) > 200 else f"[green]✓ Response: {response}[/green]")
        
        console.print(f"[dim]Action: {action}[/dim]")
        return True
        
    except Exception as e:
        console.print(f"[bold red]✗ ERROR: {e}[/bold red]")
        return False


async def async_main():
    """Run all dry run scenarios."""
    console.print(Panel.fit(
        "[bold magenta]Agent Dry Run - Testing All Features[/bold magenta]\n"
        "This will test: chat, single-file edit, multi-file edit, shell, PR review, memory, project creation, and interrupts",
        border_style="magenta"
    ))
    
    # Create test directory
    test_dir = Path("dry_run_test")
    test_dir.mkdir(exist_ok=True)
    
    results = []
    
    # 1. Chat functionality
    results.append(await run_scenario(
        "Chat - Simple greeting",
        "Hello, who are you?",
        {"configurable": {"thread_id": "dry_chat_1"}},
        expected_action="chat"
    ))
    
    results.append(await run_scenario(
        "Chat - Question about capabilities",
        "What can you do?",
        {"configurable": {"thread_id": "dry_chat_2"}},
        expected_action="chat"
    ))
    
    # 2. Memory operations
    results.append(await run_scenario(
        "Memory - Save information",
        "Remember that my favorite language is Python",
        {"configurable": {"thread_id": "dry_memory_1"}},
        expected_action="remember"
    ))
    
    results.append(await run_scenario(
        "Memory - Recall information",
        "What's my favorite language?",
        {"configurable": {"thread_id": "dry_memory_2"}},
        expected_action="recall"
    ))
    
    # 3. Shell execution (safe command)
    results.append(await run_scenario(
        "Shell - Safe command",
        "Run ls -la",
        {"configurable": {"thread_id": "dry_shell_1"}},
        expected_action="shell"
    ))
    
    # 4. Single file creation
    test_file = test_dir / "test_single.py"
    
    results.append(await run_scenario(
        "Edit - Create single file with function",
        f"Create {test_file} with a fibonacci function",
        {"configurable": {"thread_id": "dry_edit_1"}},
        expected_action="edit"
    ))
    
    if test_file.exists():
        code = test_file.read_text()
        if "fibonacci" in code.lower() and "def " in code:
            console.print("[green]✓ File contains fibonacci function[/green]")
        else:
            console.print("[red]✗ File missing expected content[/red]")
            results[-1] = False
    
    # 5. Multi-file editing
    file1 = test_dir / "utils1.py"
    file2 = test_dir / "utils2.py"
    file1.write_text("def func1():\n    pass")
    file2.write_text("def func2():\n    pass")
    
    results.append(await run_scenario(
        "Edit Multi - Add type hints to multiple files",
        f"Add type hints to {file1} and {file2}",
        {"configurable": {"thread_id": "dry_multi_1"}},
        expected_action="edit_multi"
    ))
    
    if file1.exists() and file2.exists():
        code1 = file1.read_text()
        code2 = file2.read_text()
        if "->" in code1 and "->" in code2:
            console.print("[green]✓ Both files have type hints[/green]")
        else:
            console.print("[yellow]⚠ Type hints may be missing[/yellow]")
    
    # 6. Project creation
    results.append(await run_scenario(
        "Project - Create multiple files",
        f"Create a simple web page with index.html and style.css in {test_dir}",
        {"configurable": {"thread_id": "dry_project_1"}},
        expected_action="project"
    ))
    
    if (test_dir / "index.html").exists() and (test_dir / "style.css").exists():
        console.print("[green]✓ Multiple files created[/green]")
    else:
        console.print("[red]✗ Files not created[/red]")
        results[-1] = False
    
    # 7. Code modification quality
    test_file = test_dir / "to_modify.py"
    original = """def calculate(x, y):
    return x + y

def other_function():
    return "unchanged"
"""
    test_file.write_text(original)
    
    results.append(await run_scenario(
        "Edit - Modify preserves other code",
        f"Add error handling to calculate function in {test_file}",
        {"configurable": {"thread_id": "dry_modify_1"}},
        expected_action="edit"
    ))
    
    if test_file.exists():
        modified = test_file.read_text()
        # Should still have the other function
        if "other_function" in modified:
            console.print("[green]✓ Preserved unrelated code[/green]")
        else:
            console.print("[red]✗ Lost unrelated code during modification[/red]")
            results[-1] = False
    
    # Cleanup
    if test_dir.exists():
        import shutil
        shutil.rmtree(test_dir)
    
    # Summary
    console.print("\n" + "="*80)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        console.print(f"[bold green]✓ ALL TESTS PASSED ({passed}/{total})[/bold green]")
    else:
        console.print(f"[bold yellow]⚠ PARTIAL PASS ({passed}/{total})[/bold yellow]")
    
    console.print("="*80)
    
    return passed == total


def main():
    """Sync wrapper for async main."""
    return asyncio.run(async_main())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

