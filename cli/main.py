import uuid
import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from agent.graph import agent_graph
from agent.tools.checkpoint_manager import should_resume, get_resume_info
from agent.tools.memory import get_memory_stats


console = Console()


def main():
    title = Text("Anicode(A coding Agent that uses the LangGraph framework)", style="bold magenta blink")
    
    description = Text(
        "Hey Brace & Palash! This agent can edit files, have conversations about code, and answer questions.\n"
        "My approach: Leveraging LangGraph's full capabilities including serial nodes, parallel execution, conditional edges, and reducers to build a sophisticated agent architecture.\n"
        "Watch me think in real-time as I process your requests!",
        style="bright_cyan"
    )
    subtitle = Text("Type 'exit' to quit | Ctrl+C to interrupt (auto-resumes on next message)", style="bright_cyan")
    
    console.print(Panel.fit(
        Text.assemble(title, "\n", description, "\n", subtitle),
        border_style="bright_magenta"
    ))
    
    memory_stats = get_memory_stats()
    if memory_stats.get("persistent"):
        console.print(f"[dim green]💾 Long-term memory: SQLite ({memory_stats.get('db_path')})[/dim green]")
        console.print(f"[dim green]   {memory_stats.get('total_entries', 0)} entries, {memory_stats.get('total_namespaces', 0)} namespaces[/dim green]")
    else:
        console.print(f"[dim yellow]⚠️  Long-term memory: In-memory (data lost on restart)[/dim yellow]")
    
    session_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}
    
    while True:
        try:
            user_input = console.input("\n[bold bright_cyan]>[/bold bright_cyan] ")
        except EOFError:
            console.print("\n[bright_magenta]Bye[/bright_magenta]")
            break
        except KeyboardInterrupt:
            console.print("\n[bright_magenta]Bye[/bright_magenta]")
            break
        
        if user_input.strip().lower() in ["exit", "quit"]:
            console.print("[bright_magenta]Bye[/bright_magenta]")
            break
        
        if not user_input.strip():
            continue
        
        console.print()
        node_count = 0
        
        # Check if we should resume from interrupted checkpoint
        state = agent_graph.get_state(config)
        is_resuming = should_resume(state)
        
        if is_resuming:
            resume_info = get_resume_info(state)
            console.print(f"[dim yellow]{resume_info}[/dim yellow]")
        
        try:
            # If resuming, pass None to continue from checkpoint
            # Otherwise pass new user input
            input_data = None if is_resuming else {"user_input": user_input}
            
            for event in agent_graph.stream(
                input_data,
                config=config,
                stream_mode="updates"
            ):
                node_count += 1
                
                for node_name, node_data in event.items():
                    console.print(f"[dim cyan]→ {node_name}[/dim cyan]", end=" ")
                    
                    if node_data.get("response"):
                        console.print()
                        response = node_data['response']
                        console.print(f"[bright_green]{response}[/bright_green]")
                    elif node_data.get("error"):
                        console.print()
                        console.print(f"[bold red]Error: {node_data['error']}[/bold red]")
                    else:
                        console.print("[dim]processing...[/dim]")
            
            console.print()
        
        except KeyboardInterrupt:
            console.print("\n\n[yellow]⚠ Interrupted! Checkpoint saved.[/yellow]")
            console.print("[dim]Type anything to resume from where you left off[/dim]\n")
        
        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")


if __name__ == "__main__":
    typer.run(main)
