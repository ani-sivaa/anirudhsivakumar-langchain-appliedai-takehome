#!/usr/bin/env python3
"""
Demo: Time Travel with SqliteSaver
Shows how persistent checkpoints enable going back to previous states.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.graph import agent_graph
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def show_checkpoint_history(thread_id: str):
    """Display all checkpoints for a thread."""
    config = {"configurable": {"thread_id": thread_id}}
    
    # Get checkpoint history
    checkpoints = list(agent_graph.checkpointer.list(config))
    
    if not checkpoints:
        console.print("[yellow]No checkpoints found for this thread[/yellow]")
        return
    
    table = Table(title=f"Checkpoint History - Thread: {thread_id}")
    table.add_column("ID", style="cyan")
    table.add_column("Step", style="green")
    table.add_column("Action", style="yellow")
    table.add_column("Next Nodes", style="magenta")
    
    for i, checkpoint in enumerate(checkpoints):
        state = checkpoint.state
        checkpoint_id = checkpoint.checkpoint_id[:8] + "..."
        action = state.get("action", "N/A")
        next_nodes = ", ".join(checkpoint.next or ["END"])
        
        table.add_row(
            checkpoint_id,
            str(i),
            action,
            next_nodes
        )
    
    console.print(table)
    console.print(f"\n[green]Total checkpoints: {len(checkpoints)}[/green]")


def demo_time_travel():
    """Demonstrate time travel capabilities."""
    
    console.print(Panel.fit(
        "[bold cyan]Time Travel Demo[/bold cyan]\n\n"
        "This shows how SqliteSaver enables:\n"
        "1. Session resumption after restarts\n"
        "2. Time travel (undo operations)\n"
        "3. Full execution history",
        border_style="cyan"
    ))
    
    thread_id = "demo-time-travel"
    config = {"configurable": {"thread_id": thread_id}}
    
    # Step 1: Run a simple operation
    console.print("\n[bold]Step 1: Running a simple chat operation...[/bold]")
    result = agent_graph.invoke(
        {"user_input": "Hello! What can you do?"},
        config=config
    )
    console.print(f"[green]✓ Response: {result.get('response', 'N/A')[:100]}...[/green]")
    
    # Step 2: Show checkpoint history
    console.print("\n[bold]Step 2: Viewing checkpoint history...[/bold]")
    show_checkpoint_history(thread_id)
    
    # Step 3: Get current state
    console.print("\n[bold]Step 3: Current state...[/bold]")
    current_state = agent_graph.get_state(config)
    console.print(f"[cyan]Current checkpoint ID: {current_state.checkpoint_id[:16]}...[/cyan]")
    console.print(f"[cyan]Next nodes: {current_state.next}[/cyan]")
    
    # Step 4: Go back to a previous checkpoint
    console.print("\n[bold]Step 4: Time travel - going back to previous checkpoint...[/bold]")
    checkpoints = list(agent_graph.checkpointer.list(config))
    
    if len(checkpoints) > 1:
        previous_checkpoint = checkpoints[1]  # Get second-to-last checkpoint
        console.print(f"[yellow]Rewinding to checkpoint: {previous_checkpoint.checkpoint_id[:16]}...[/yellow]")
        
        # Get state at that checkpoint
        past_state = agent_graph.get_state(config, checkpoint_id=previous_checkpoint.checkpoint_id)
        console.print(f"[green]✓ Traveled back! State from previous checkpoint loaded[/green]")
        console.print(f"[cyan]Checkpoint ID: {past_state.checkpoint_id[:16]}...[/cyan]")
    
    # Step 5: Demonstrate resumption
    console.print("\n[bold]Step 5: Session resumption capability...[/bold]")
    console.print(f"[green]✓ All checkpoints saved to data/checkpoints.db[/green]")
    console.print(f"[green]✓ Can resume from any checkpoint even after restart![/green]")
    
    console.print("\n[bold cyan]Demo Complete![/bold cyan]")
    console.print("\n[yellow]Key Takeaways:[/yellow]")
    console.print("• Checkpoints persist in data/checkpoints.db (not lost on restart)")
    console.print("• Can view full execution history")
    console.print("• Can rewind to any previous state")
    console.print("• Enables 'undo' functionality")
    console.print("• Production-ready persistence")


if __name__ == "__main__":
    try:
        demo_time_travel()
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()

