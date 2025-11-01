#!/usr/bin/env python
"""
Demo script showing streaming with interrupt & resume capabilities.
"""

from rich.console import Console
from agent.graph import agent_graph

console = Console()


def demo_streaming():
    console.print("\n[bold cyan]═══════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold magenta]  Streaming Demo: Watch Agent Think in Real-Time  [/bold magenta]")
    console.print("[bold cyan]═══════════════════════════════════════════════════[/bold cyan]\n")
    
    thread_id = "demo-stream-001"
    config = {"configurable": {"thread_id": thread_id}}
    
    console.print(f"[cyan]Session ID:[/cyan] [bold]{thread_id}[/bold]")
    console.print("[dim]Watch each node execute in sequence...[/dim]\n")
    
    user_input = "Tell me a joke about Python programming"
    console.print(f"[green]User:[/green] {user_input}\n")
    
    node_count = 0
    
    try:
        for event in agent_graph.stream(
            {"user_input": user_input},
            config=config,
            stream_mode="updates"
        ):
            node_count += 1
            
            for node_name, node_data in event.items():
                console.print(f"[bold cyan]→ Node {node_count}:[/bold cyan] [magenta]{node_name}[/magenta]")
                
                if node_data.get("action"):
                    console.print(f"   [dim]Action: {node_data['action']}[/dim]")
                
                if node_data.get("response"):
                    response = node_data['response']
                    console.print(f"   [green]Response: {response[:100]}...[/green]")
                
                console.print()
        
        console.print("[bold green]✓ Execution complete![/bold green]\n")
        
        state = agent_graph.get_state(config)
        console.print(f"[cyan]Final state saved at checkpoint[/cyan]")
        console.print(f"[cyan]Total nodes executed:[/cyan] {node_count}")
        
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠ Interrupted by user![/yellow]")
        
        state = agent_graph.get_state(config)
        console.print(f"\n[green]Session saved! Can resume later.[/green]")
        console.print(f"[cyan]Thread ID:[/cyan] {thread_id}")
        console.print(f"[cyan]Nodes executed:[/cyan] {node_count}")


def demo_inspect():
    console.print("\n[bold cyan]═══════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold magenta]  State Inspection: View Saved Checkpoints  [/bold magenta]")
    console.print("[bold cyan]═══════════════════════════════════════════════════[/bold cyan]\n")
    
    thread_id = "demo-stream-001"
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        state = agent_graph.get_state(config)
        
        console.print(f"[bold cyan]Session:[/bold cyan] {thread_id}")
        console.print(f"[cyan]Next node to execute:[/cyan] {state.next}")
        
        console.print(f"\n[bold cyan]Key State Values:[/bold cyan]")
        if state.values.get("user_input"):
            console.print(f"  User Input: {state.values['user_input']}")
        if state.values.get("action"):
            console.print(f"  Action: {state.values['action']}")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")


if __name__ == "__main__":
    console.print("\n[bold]LangGraph Streaming Capabilities Demo[/bold]\n")
    
    demo_streaming()
    
    console.print("\n" + "="*50 + "\n")
    
    demo_inspect()
    
    console.print("\n[bold green]✓ Demo complete![/bold green]")
    console.print("\n[cyan]Try it yourself:[/cyan]")
    console.print("  python -m cli.main chat --stream")
    console.print("\n")

