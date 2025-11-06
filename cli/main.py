import uuid
import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from agent.graph import agent_graph
from agent.tools.checkpoint_manager import should_resume, get_resume_info
from agent.tools.memory import get_memory_stats
from agent.tools.codebase_indexer import index_codebase, search_codebase


console = Console()


def auto_index_codebase():
    """Auto-index the codebase on startup."""
    console.print("[dim yellow]Indexing codebase for semantic search...[/dim yellow]")
    result = index_codebase(".")

    if result.get("error"):
        console.print(f"[dim red]Indexing failed: {result['error']}[/dim red]")
    else:
        console.print(f"[dim green]Indexed {result.get('total_files', 0)} files successfully[/dim green]")


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
        console.print(f"[dim green]Long-term memory: SQLite ({memory_stats.get('db_path')})[/dim green]")
        console.print(f"[dim green]   {memory_stats.get('total_entries', 0)} entries, {memory_stats.get('total_namespaces', 0)} namespaces[/dim green]")
    else:
        console.print(f"[dim yellow]Long-term memory: In-memory (data lost on restart)[/dim yellow]")

    # Auto-index codebase on startup
    auto_index_codebase()

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
        
        # Only resume if there are actual pending nodes AND it's not already been processed
        # If state.next is empty or None, the graph has finished and we should start fresh
        is_resuming = False
        if state.next and len(state.next) > 0:
            # Check if this is a stale approval request (already denied/approved)
            # If approval_response exists in state, we've already processed this approval
            if "request_approval" in state.next:
                approval_response = state.values.get("approval_response")
                if approval_response:
                    # This approval was already processed - don't resume it
                    # Start fresh with new input
                    is_resuming = False
                else:
                    # Real pending approval - resume
                    is_resuming = True
                    resume_info = get_resume_info(state)
                    console.print(f"[dim yellow]{resume_info}[/dim yellow]")
            else:
                # Other pending nodes - resume normally
                is_resuming = True
                resume_info = get_resume_info(state)
                console.print(f"[dim yellow]{resume_info}[/dim yellow]")
        
        try:
            # If resuming, pass None to continue from checkpoint
            # Otherwise pass new user input
            input_data = None if is_resuming else {"user_input": user_input}
            
            interrupted = False
            for event in agent_graph.stream(
                input_data,
                config=config,
                stream_mode="updates"
            ):
                node_count += 1
                
                for node_name, node_data in event.items():
                    # Check if this is an interrupt event
                    if node_name == "__interrupt__":
                        interrupted = True
                        console.print()
                        
                        # Get the current state to access approval_request
                        state = agent_graph.get_state(config)
                        approval_request = state.values.get("approval_request", {})
                        
                        if approval_request:
                            console.print(Panel.fit(
                                Text.assemble(
                                    Text("APPROVAL REQUIRED\n\n", style="bold yellow"),
                                    Text(f"Type: ", style="dim"),
                                    Text(f"{approval_request.get('type', 'unknown')}\n", style="bright_white"),
                                    Text(f"Warning: ", style="dim"),
                                    Text(f"{approval_request.get('warning', '')}\n\n", style="bold red"),
                                    Text(f"{approval_request.get('question', 'Approve this operation?')}\n", style="bright_yellow"),
                                    Text(f"\nCommand: ", style="dim") if approval_request.get('command') else Text(""),
                                    Text(f"{approval_request.get('command', '')}\n", style="bright_red") if approval_request.get('command') else Text(""),
                                    Text(f"\nFile: ", style="dim") if approval_request.get('path') else Text(""),
                                    Text(f"{approval_request.get('path', '')}\n", style="bright_cyan") if approval_request.get('path') else Text(""),
                                ),
                                border_style="bold yellow",
                                title="[bold yellow]Human Approval Needed[/bold yellow]"
                            ))
                            
                            # Get user's decision
                            while True:
                                decision = console.input("\n[bold bright_yellow]Approve? (yes/no):[/bold bright_yellow] ").strip().lower()
                                if decision in ['yes', 'y', 'approve']:
                                    approval_response = "approve"
                                    break
                                elif decision in ['no', 'n', 'deny', 'cancel']:
                                    approval_response = "deny"
                                    break
                                else:
                                    console.print("[dim red]Please answer 'yes' or 'no'[/dim red]")
                            
                            # Update state with user's decision
                            agent_graph.update_state(config, {"approval_response": approval_response})
                            
                            # Show status
                            console.print()
                            if approval_response == "approve":
                                console.print("[dim green]Approved - resuming execution...[/dim green]\n")
                            else:
                                console.print("[dim red]Denied - cancelling operation...[/dim red]\n")
                            
                            # Resume execution and make sure we fully drain the stream
                            for resume_event in agent_graph.stream(None, config=config, stream_mode="updates"):
                                for resume_node_name, resume_node_data in resume_event.items():
                                    # Skip any __interrupt__ events in resume - they're already handled
                                    if resume_node_name == "__interrupt__":
                                        continue
                                    
                                    console.print(f"[dim cyan]→ {resume_node_name}[/dim cyan]", end=" ")
                                    
                                    if isinstance(resume_node_data, dict):
                                        if resume_node_data.get("response"):
                                            console.print()
                                            response = resume_node_data['response']
                                            console.print(f"[bright_green]{response}[/bright_green]")
                                        elif resume_node_data.get("error"):
                                            console.print()
                                            console.print(f"[bold red]Error: {resume_node_data['error']}[/bold red]")
                                        else:
                                            console.print("[dim]processing...[/dim]")
                                    else:
                                        console.print("[dim]processing...[/dim]")
                        break
                    
                    # Normal node execution
                    console.print(f"[dim cyan]→ {node_name}[/dim cyan]", end=" ")
                    
                    # Check if node_data is a dict (some nodes might return None or other types)
                    if isinstance(node_data, dict):
                        if node_data.get("response"):
                            console.print()
                            response = node_data['response']
                            console.print(f"[bright_green]{response}[/bright_green]")
                        elif node_data.get("error"):
                            console.print()
                            console.print(f"[bold red]Error: {node_data['error']}[/bold red]")
                        else:
                            console.print("[dim]processing...[/dim]")
                    else:
                        console.print("[dim]processing...[/dim]")
                
                # If interrupted, we handled the rest in the loop above
                if interrupted:
                    break
            
            if not interrupted:
                console.print()
        
        except KeyboardInterrupt:
            console.print("\n\n[yellow]Interrupted! Checkpoint saved.[/yellow]")
            console.print("[dim]Type anything to resume from where you left off[/dim]\n")
        
        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")


if __name__ == "__main__":
    typer.run(main)
