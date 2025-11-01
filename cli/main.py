import uuid
import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from agent.graph import agent_graph


console = Console()


def main():
    title = Text("Anirudh's Jarvis (Coding Agent that uses the LangGraph framework)", style="bold magenta blink")
    
    description = Text(
        "Hey Brace & Palash! This agent can edit files, have conversations about code, and answer questions.\n"
        "My approach: Leveraging LangGraph's full capabilities including serial nodes, parallel execution, conditional edges, and reducers to build a sophisticated agent architecture.\n"
        "Watch me think in real-time as I process your requests!",
        style="bright_cyan"
    )
    subtitle = Text("Type 'exit' to quit | Ctrl+C to interrupt and save", style="bright_cyan")
    
    console.print(Panel.fit(
        Text.assemble(title, "\n", description, "\n", subtitle),
        border_style="bright_magenta"
    ))
    
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
        
        try:
            for event in agent_graph.stream(
                {"user_input": user_input},
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
            console.print("\n\n[yellow]⚠ Interrupted! Session saved at checkpoint.[/yellow]")
            state = agent_graph.get_state(config)
            console.print(f"[cyan]Session ID: {session_id}[/cyan]")
            console.print("[dim]Continue by restarting - your conversation is saved![/dim]\n")
        
        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")


if __name__ == "__main__":
    typer.run(main)
