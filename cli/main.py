import uuid
import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.prompt import Prompt, Confirm
from datetime import datetime

from agent.graph import agent_graph
from agent.tools.checkpoint_manager import should_resume, get_resume_info
from agent.tools.memory import get_memory_stats
from agent.tools.codebase_indexer import index_codebase, search_codebase
from agent.tools.thread_manager import get_thread_manager


console = Console()


def show_thread_menu() -> tuple[str, str]:
    """
    Show thread selection menu and return (thread_id, thread_name).
    
    Returns:
        tuple: (thread_id, thread_name)
    """
    thread_mgr = get_thread_manager()
    recent_threads = thread_mgr.list_threads(limit=10)
    
    if not recent_threads:
        # No threads exist - create first one
        console.print("[dim yellow]No previous conversations found. Starting new conversation![/dim yellow]\n")
        thread_id = thread_mgr.create_thread(thread_name="First Conversation")
        return thread_id, "First Conversation"
    
    # Show recent threads table
    console.print("\n[bold cyan]📚 Recent Conversations:[/bold cyan]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=3)
    table.add_column("Name", style="cyan", width=40)
    table.add_column("Messages", justify="right", width=8)
    table.add_column("Last Used", style="dim", width=20)
    
    for idx, thread in enumerate(recent_threads, 1):
        last_used = datetime.fromisoformat(thread['last_used'])
        time_ago = format_time_ago(last_used)
        
        table.add_row(
            str(idx),
            thread['thread_name'],
            str(thread['message_count']),
            time_ago
        )
    
    console.print(table)
    console.print()
    
    # Prompt for selection
    console.print("[dim]Enter a number to resume, or press Enter for new conversation[/dim]")
    choice = Prompt.ask("[bold cyan]Choice[/bold cyan]", default="new")
    
    if choice.lower() in ["new", "n", ""]:
        # Create new thread
        thread_id = thread_mgr.create_thread()
        return thread_id, thread_mgr.get_thread_by_id(thread_id)['thread_name']
    
    try:
        idx = int(choice)
        if 1 <= idx <= len(recent_threads):
            selected = recent_threads[idx - 1]
            console.print(f"[dim green]Resuming: {selected['thread_name']}[/dim green]\n")
            return selected['thread_id'], selected['thread_name']
    except ValueError:
        pass
    
    # Invalid choice - create new
    console.print("[dim yellow]Invalid choice. Starting new conversation.[/dim yellow]\n")
    thread_id = thread_mgr.create_thread()
    return thread_id, thread_mgr.get_thread_by_id(thread_id)['thread_name']


def format_time_ago(dt: datetime) -> str:
    """Format datetime as human-readable time ago."""
    now = datetime.now()
    
    # Handle ISO string or datetime object
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    
    diff = now - dt
    
    if diff.days > 365:
        return f"{diff.days // 365}y ago"
    elif diff.days > 30:
        return f"{diff.days // 30}mo ago"
    elif diff.days > 0:
        return f"{diff.days}d ago"
    elif diff.seconds > 3600:
        return f"{diff.seconds // 3600}h ago"
    elif diff.seconds > 60:
        return f"{diff.seconds // 60}m ago"
    else:
        return "just now"


def handle_special_command(command: str, current_thread_id: str, current_thread_name: str) -> tuple[bool, str, str]:
    """
    Handle special commands like /list, /rename, /switch, /new.
    
    Returns:
        tuple: (handled: bool, new_thread_id: str, new_thread_name: str)
    """
    thread_mgr = get_thread_manager()
    
    if command == "/list":
        threads = thread_mgr.list_threads(limit=20)
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan", width=40)
        table.add_column("Messages", justify="right", width=8)
        table.add_column("Last Used", style="dim", width=20)
        table.add_column("ID", style="dim", width=36)
        
        for thread in threads:
            last_used = datetime.fromisoformat(thread['last_used'])
            time_ago = format_time_ago(last_used)
            
            # Highlight current thread
            name_style = "bold cyan" if thread['thread_id'] == current_thread_id else "cyan"
            name = f"→ {thread['thread_name']}" if thread['thread_id'] == current_thread_id else thread['thread_name']
            
            table.add_row(
                name,
                str(thread['message_count']),
                time_ago,
                thread['thread_id'][:8] + "..."
            )
        
        console.print(table)
        return True, current_thread_id, current_thread_name
    
    elif command.startswith("/rename "):
        new_name = command[8:].strip()
        if new_name:
            thread_mgr.rename_thread(current_thread_id, new_name)
            console.print(f"[dim green]Renamed to: {new_name}[/dim green]")
            return True, current_thread_id, new_name
        else:
            console.print("[dim red]Usage: /rename <new name>[/dim red]")
            return True, current_thread_id, current_thread_name
    
    elif command.startswith("/switch "):
        target = command[8:].strip()
        
        # Try as number first (from /list)
        threads = thread_mgr.list_threads(limit=20)
        try:
            idx = int(target)
            if 1 <= idx <= len(threads):
                thread = threads[idx - 1]
                console.print(f"[dim green]Switched to: {thread['thread_name']}[/dim green]")
                return True, thread['thread_id'], thread['thread_name']
        except ValueError:
            # Try as name
            thread = thread_mgr.get_thread_by_name(target)
            if thread:
                console.print(f"[dim green]Switched to: {thread['thread_name']}[/dim green]")
                return True, thread['thread_id'], thread['thread_name']
        
        console.print("[dim red]Thread not found. Use /list to see available threads.[/dim red]")
        return True, current_thread_id, current_thread_name
    
    elif command == "/new":
        # Create new thread
        thread_id = thread_mgr.create_thread()
        thread_name = thread_mgr.get_thread_by_id(thread_id)['thread_name']
        console.print(f"[dim green]Started new conversation: {thread_name}[/dim green]")
        return True, thread_id, thread_name
    
    elif command == "/help":
        console.print(Panel.fit(
            """[bold cyan]Thread Management Commands:[/bold cyan]

[bold]/list[/bold]              - List all conversations
[bold]/rename <name>[/bold]     - Rename current conversation
[bold]/switch <name|#>[/bold]   - Switch to another conversation
[bold]/new[/bold]               - Start a new conversation
[bold]/help[/bold]              - Show this help message
[bold]exit[/bold]               - Quit the application

[dim]Regular messages are sent to the agent.[/dim]""",
            border_style="cyan",
            title="[bold]Help[/bold]"
        ))
        return True, current_thread_id, current_thread_name
    
    return False, current_thread_id, current_thread_name


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
    subtitle = Text("Type 'exit' to quit | '/help' for commands | Ctrl+C to interrupt", style="bright_cyan")

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

    # Thread selection
    thread_id, thread_name = show_thread_menu()
    thread_mgr = get_thread_manager()
    
    config = {"configurable": {"thread_id": thread_id}}
    
    # Show current thread name in status
    console.print(f"[dim cyan]Current conversation: {thread_name}[/dim cyan]")
    console.print(f"[dim]Type /help to see thread management commands[/dim]\n")
    
    while True:
        try:
            user_input = console.input("\n[bold bright_cyan]>[/bold bright_cyan] ")
        except EOFError:
            console.print("\n[bright_magenta]Bye[/bright_magenta]")
            break
        except KeyboardInterrupt:
            # Ctrl+C at input prompt - ask if they want to quit
            console.print()
            try:
                confirm = console.input("[dim yellow]Quit? (y/n):[/dim yellow] ").strip().lower()
                if confirm in ['y', 'yes']:
                    console.print("[bright_magenta]Bye[/bright_magenta]")
                    break
                else:
                    continue
            except (KeyboardInterrupt, EOFError):
                console.print("\n[bright_magenta]Bye[/bright_magenta]")
                break
        
        if user_input.strip().lower() in ["exit", "quit"]:
            console.print("[bright_magenta]Bye[/bright_magenta]")
            break
        
        if not user_input.strip():
            continue
        
        # Handle special commands
        if user_input.strip().startswith("/"):
            handled, thread_id, thread_name = handle_special_command(
                user_input.strip(), 
                thread_id, 
                thread_name
            )
            if handled:
                # Update config if thread changed
                config = {"configurable": {"thread_id": thread_id}}
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
            if is_resuming:
                input_data = None
            else:
                # Just pass user input - LangGraph will merge with checkpoint state
                # The nodes themselves will add to messages via the 'add' reducer
                input_data = {"user_input": user_input}
            
            # Update thread metadata - auto-name if first message
            thread = thread_mgr.get_thread_by_id(thread_id)
            if thread and thread['message_count'] == 0 and not is_resuming:
                # First message - auto-name the thread
                new_name = thread_mgr._generate_name_from_message(user_input)
                thread_mgr.rename_thread(thread_id, new_name)
                thread_name = new_name
            
            # Update activity
            if not is_resuming:
                thread_mgr.update_thread_activity(thread_id)
            
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
            console.print("\n\n[yellow]⏸️  Interrupted! Checkpoint saved.[/yellow]")
            console.print("[dim]Your progress is saved. Continue typing to resume, or press Ctrl+C again to quit.[/dim]")
            # Stay in the loop - don't break!
            # Next message will resume from checkpoint
        
        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")


if __name__ == "__main__":
    typer.run(main)
