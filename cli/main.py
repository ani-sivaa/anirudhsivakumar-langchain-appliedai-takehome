import uuid
import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from agent.graph import agent_graph


app = typer.Typer()
console = Console()


def main():
    title = Text("Anirudh's Jarvis (Coding Agent that uses the LangGraph framework)", style="bold magenta blink")
    description = Text("Hey Brace & Palash! This agent can edit files, have conversations about code, and answer questions.\nMy approach: Leveraging LangGraph's full capabilities including serial nodes, parallel execution, conditional edges, and reducers to build a sophisticated agent architecture.", style="bright_cyan")
    subtitle = Text("Type 'exit' to quit", style="bright_cyan")
    
    console.print(Panel.fit(
        Text.assemble(title, "\n", description, "\n", subtitle),
        border_style="bright_magenta"
    ))
    
    session_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}
    
    while True:
        try:
            user_input = console.input("\n[bold bright_cyan]>[/bold bright_cyan] ")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[bright_magenta]Bye[/bright_magenta]")
            break
        
        if user_input.strip().lower() in ["exit", "quit"]:
            console.print("[bright_magenta]Bye[/bright_magenta]")
            break
        
        if not user_input.strip():
            continue
        
        try:
            result = agent_graph.invoke(
                {"user_input": user_input},
                config=config
            )
            
            response = result.get("response", "")
            if response:
                console.print(f"[bright_green]{response}[/bright_green]")
            
            error = result.get("error", "")
            if error:
                console.print(f"[bold red]Error: {error}[/bold red]")
                
        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")


if __name__ == "__main__":
    typer.run(main)
