import os
import sys
import uuid
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

from agent.graph import agent_graph


app = typer.Typer()
console = Console()


def show_header():
    title = Text("Anirudh's Jarvis", style="bold cyan")
    title.append(" - Streaming Mode", style="bold magenta")
    
    desc = Text()
    desc.append("Live execution with interrupt & resume capability\n\n", style="bold red")
    desc.append("Features:\n", style="bold white")
    desc.append("• Watch agent think in real-time\n", style="cyan")
    desc.append("• Press Ctrl+C to interrupt execution\n", style="yellow")
    desc.append("• Resume from exact checkpoint later\n", style="green")
    desc.append("• Full persistence across sessions\n", style="blue")
    
    console.print(Panel(desc, title=str(title), border_style="cyan"))


@app.command()
def run(
    user_input: str = typer.Argument(..., help="Your request to the agent"),
    thread_id: Optional[str] = typer.Option(None, help="Session ID to resume"),
    resume_from: Optional[str] = typer.Option(None, help="Checkpoint ID to resume from")
):
    """
    Run agent with streaming execution visualization.
    """
    
    if not thread_id:
        thread_id = f"stream-{uuid.uuid4().hex[:8]}"
    
    console.print(f"\n[cyan]Session ID:[/cyan] [bold]{thread_id}[/bold]")
    console.print(f"[cyan]Input:[/cyan] {user_input}\n")
    
    config = {"configurable": {"thread_id": thread_id}}
    
    if resume_from:
        console.print(f"[green]Resuming from checkpoint:[/green] {resume_from}\n")
    
    try:
        node_count = 0
        current_node = None
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            task = progress.add_task("[cyan]Starting...", total=None)
            
            for event in agent_graph.stream(
                {"user_input": user_input},
                config=config,
                stream_mode="updates"
            ):
                node_count += 1
                
                for node_name, node_data in event.items():
                    current_node = node_name
                    
                    progress.update(
                        task,
                        description=f"[cyan]Node {node_count}: [bold magenta]{node_name}[/bold magenta]"
                    )
                    
                    console.print(f"\n[bold green]→ Executing:[/bold green] [magenta]{node_name}[/magenta]")
                    
                    if node_data.get("action"):
                        console.print(f"  [dim]Action: {node_data['action']}[/dim]")
                    
                    if node_data.get("response"):
                        response = node_data['response']
                        if len(response) > 200:
                            response = response[:200] + "..."
                        console.print(f"  [dim]Response: {response}[/dim]")
                    
                    if node_data.get("error"):
                        console.print(f"  [red]Error: {node_data['error']}[/red]")
        
        console.print("\n[bold green]✓ Execution complete![/bold green]")
        
        state = agent_graph.get_state(config)
        console.print(f"\n[cyan]Final checkpoint:[/cyan] {state.config['configurable'].get('checkpoint_id', 'N/A')}")
        console.print(f"[cyan]Session saved as:[/cyan] [bold]{thread_id}[/bold]")
        
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠ Interrupted by user![/yellow]")
        
        state = agent_graph.get_state(config)
        checkpoint_id = state.config['configurable'].get('checkpoint_id')
        
        console.print(f"\n[green]Session saved at checkpoint:[/green] {checkpoint_id}")
        console.print(f"[green]Last executed node:[/green] {current_node}")
        
        console.print(f"\n[cyan]To resume:[/cyan]")
        console.print(f"  python -m cli.streaming run '{user_input}' --thread-id {thread_id}")
        
        sys.exit(0)
    
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {str(e)}")
        sys.exit(1)


@app.command()
def inspect(thread_id: str = typer.Argument(..., help="Session ID to inspect")):
    """
    Inspect a session's state and checkpoints.
    """
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        state = agent_graph.get_state(config)
        
        console.print(f"\n[bold cyan]Session:[/bold cyan] {thread_id}")
        console.print(f"[cyan]Checkpoint ID:[/cyan] {state.config['configurable'].get('checkpoint_id', 'N/A')}")
        console.print(f"[cyan]Next node:[/cyan] {state.next}")
        
        console.print(f"\n[bold cyan]State Values:[/bold cyan]")
        for key, value in state.values.items():
            if key in ["user_input", "action", "response", "error"]:
                val_str = str(value)
                if len(val_str) > 100:
                    val_str = val_str[:100] + "..."
                console.print(f"  {key}: {val_str}")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        sys.exit(1)


@app.command()
def interactive():
    """
    Interactive streaming mode with live updates.
    """
    show_header()
    
    thread_id = f"interactive-{uuid.uuid4().hex[:8]}"
    console.print(f"\n[cyan]Session ID:[/cyan] [bold]{thread_id}[/bold]")
    console.print("[dim]Type 'exit' to quit, Ctrl+C to interrupt[/dim]\n")
    
    while True:
        try:
            user_input = console.input("[bold green]You:[/bold green] ")
            
            if user_input.lower() in ["exit", "quit", "bye"]:
                console.print("[cyan]Goodbye![/cyan]")
                break
            
            if not user_input.strip():
                continue
            
            console.print()
            
            config = {"configurable": {"thread_id": thread_id}}
            node_count = 0
            
            try:
                for event in agent_graph.stream(
                    {"user_input": user_input},
                    config=config,
                    stream_mode="updates"
                ):
                    node_count += 1
                    
                    for node_name, node_data in event.items():
                        console.print(f"[dim]→ {node_name}[/dim]")
                        
                        if node_data.get("response"):
                            response = node_data['response']
                            console.print(f"\n[bold cyan]Jarvis:[/bold cyan] {response}\n")
                
            except KeyboardInterrupt:
                console.print("\n[yellow]⚠ Interrupted! Continuing...[/yellow]\n")
                continue
        
        except KeyboardInterrupt:
            console.print("\n[cyan]Goodbye![/cyan]")
            break
        except EOFError:
            console.print("\n[cyan]Goodbye![/cyan]")
            break


if __name__ == "__main__":
    app()

