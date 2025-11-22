import asyncio
import aiosqlite
from langgraph.graph import StateGraph, END, START
from langgraph.types import Send
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from agent.state import AgentState
from agent.nodes.intent import determine_intent
from agent.nodes.chat import chat_response
from agent.nodes.file_io import read_file, write_file, read_file_multi, write_file_multi
from agent.nodes.modify import modify_code, modify_code_multi
from agent.nodes.shell import run_shell
from agent.nodes.install import install_dependency, should_retry_with_install, prepare_retry
from agent.nodes.summarize_edit import summarize_multi_edit
from agent.nodes.edit_multi_passthrough import edit_multi_passthrough
from agent.nodes.edit_multi_stages import edit_multi_modify_passthrough, edit_multi_write_passthrough
from agent.nodes.memory_ops import save_user_memory, recall_user_memory
from agent.nodes.project import plan_project, create_project_file, collect_project_files, summarize_project
from agent.nodes.approval import check_approval_needed, request_approval, route_approval, route_after_approval, handle_denial
from agent.nodes.auto_memory_update import auto_update_project_memory, recall_project_context
from agent.nodes.codebase_chat import chat_about_codebase, index_codebase_node
from agent.tools.memory import get_memory_store


def fan_out_project_files(state: AgentState):
    """Creates parallel create_file instances - one per planned file."""
    files = state.get("project_files", [])
    return [Send("create_file", {"file_path": f["path"], "file_description": f["description"]}) for f in files]


def fan_out_read_multi(state: AgentState):
    """Creates parallel read_file_multi instances - one per file to edit."""
    paths = state.get("paths", [])
    # Send() only passes the dict provided, not the full state
    # We only need path for read operations
    return [Send("read_file_multi", {"path": path}) for path in paths]


def fan_out_modify_multi(state: AgentState):
    """Creates parallel modify_code_multi instances - one per file."""
    paths = state.get("paths", [])
    contents = state.get("contents", {})
    instruction = state.get("edit_instruction", "")
    
    # Send() needs ALL the data the modify node will need
    # Can't rely on state being passed through - must include it explicitly
    return [
        Send("modify_code_multi", {
            "path": path,
            "contents": contents,
            "edit_instruction": instruction
        }) 
        for path in paths
    ]


def fan_out_write_multi(state: AgentState):
    """Creates parallel write_file_multi instances - one per file."""
    paths = state.get("paths", [])
    modifications = state.get("modifications", {})
    
    # Send() needs the modifications dict so write nodes can access it
    return [
        Send("write_file_multi", {
            "path": path,
            "modifications": modifications
        }) 
        for path in paths
    ]


async def create_graph():
    """
    Builds the main LangGraph StateGraph with all nodes and edges.
    This is where the magic happens - defines all the workflows and how they connect.
    """
    graph = StateGraph(AgentState)
    
    graph.add_node("determine_intent", determine_intent)
    graph.add_node("check_approval", check_approval_needed)
    graph.add_node("request_approval", request_approval)
    graph.add_node("denied", handle_denial)
    graph.add_node("chat", chat_response)
    graph.add_node("read_file", read_file)
    graph.add_node("modify_code", modify_code)
    graph.add_node("write_file", write_file)
    graph.add_node("edit_multi", edit_multi_passthrough)
    graph.add_node("read_file_multi", read_file_multi)
    graph.add_node("edit_multi_modify", edit_multi_modify_passthrough)
    graph.add_node("modify_code_multi", modify_code_multi)
    graph.add_node("edit_multi_write", edit_multi_write_passthrough)
    graph.add_node("write_file_multi", write_file_multi)
    graph.add_node("summarize_multi_edit", summarize_multi_edit)
    graph.add_node("shell", run_shell)
    graph.add_node("install", install_dependency)
    graph.add_node("prepare_retry", prepare_retry)
    graph.add_node("save_memory", save_user_memory)
    graph.add_node("recall_memory", recall_user_memory)
    graph.add_node("plan_project", plan_project)
    graph.add_node("create_file", create_project_file)
    graph.add_node("collect_project_files", collect_project_files)
    graph.add_node("summarize_project", summarize_project)
    graph.add_node("auto_memory", auto_update_project_memory)
    graph.add_node("project_context", recall_project_context)
    graph.add_node("index_codebase", index_codebase_node)
    graph.add_node("ask_codebase", chat_about_codebase)

    graph.add_edge(START, "determine_intent")
    graph.add_edge("determine_intent", "check_approval")
    
    graph.add_conditional_edges(
        "check_approval",
        route_approval,
        {
            "chat": "chat",
            "read_file": "read_file",
            "edit_multi": "edit_multi",
            "shell": "shell",
            "install": "install",
            "remember": "save_memory",
            "recall": "recall_memory",
            "project": "plan_project",
            "project_context": "project_context",
            "index_codebase": "index_codebase",
            "ask_codebase": "ask_codebase",
            "request_approval": "request_approval"
        }
    )
    
    graph.add_conditional_edges(
        "request_approval",
        route_after_approval,
        {
            "chat": "chat",
            "read_file": "read_file",
            "edit_multi": "edit_multi",
            "shell": "shell",
            "install": "install",
            "remember": "save_memory",
            "recall": "recall_memory",
            "project": "plan_project",
            "project_context": "project_context",
            "index_codebase": "index_codebase",
            "ask_codebase": "ask_codebase",
            "denied": "denied"
        }
    )
    
    graph.add_edge("chat", END)
    graph.add_edge("save_memory", END)
    graph.add_edge("recall_memory", END)
    graph.add_edge("denied", END)
    graph.add_edge("project_context", END)
    graph.add_edge("index_codebase", END)
    graph.add_edge("ask_codebase", END)
    
    graph.add_edge("read_file", "modify_code")
    graph.add_edge("modify_code", "write_file")
    graph.add_edge("write_file", "auto_memory")
    graph.add_edge("auto_memory", END)
    
    # Multi-file edit: single fan-out per stage, not per node
    graph.add_conditional_edges("edit_multi", fan_out_read_multi, ["read_file_multi"])
    graph.add_edge("read_file_multi", "edit_multi_modify")  # Collect all reads first
    graph.add_conditional_edges("edit_multi_modify", fan_out_modify_multi, ["modify_code_multi"])
    graph.add_edge("modify_code_multi", "edit_multi_write")  # Collect all modifies first
    graph.add_conditional_edges("edit_multi_write", fan_out_write_multi, ["write_file_multi"])
    graph.add_edge("write_file_multi", "summarize_multi_edit")
    graph.add_edge("summarize_multi_edit", "auto_memory")
    graph.add_edge("auto_memory", END)
    
    graph.add_conditional_edges("plan_project", fan_out_project_files, ["create_file"])
    graph.add_edge("create_file", "collect_project_files")  # Collect all creates first
    graph.add_edge("collect_project_files", "summarize_project")  # Then summarize once
    graph.add_edge("summarize_project", "auto_memory")
    graph.add_edge("auto_memory", END)
    
    # Auto-heal loop: shell → (check if retry needed) → prepare_retry → install → shell (retry)
    def route_shell_result(state: AgentState) -> str:
        """Decides whether to retry shell command with package install or end."""
        if should_retry_with_install(state):
            return "prepare_retry"
        return "end_shell"
    
    graph.add_conditional_edges("shell", route_shell_result, {"prepare_retry": "prepare_retry", "end_shell": END})
    graph.add_edge("prepare_retry", "install")
    graph.add_edge("install", "shell")  # Retry the command after install
    
    # AsyncSqliteSaver initialization
    # Create connection using aiosqlite and initialize checkpointer
    conn = await aiosqlite.connect("./data/checkpoints.db")
    checkpointer = AsyncSqliteSaver(conn)
    store = get_memory_store()
    return graph.compile(checkpointer=checkpointer, store=store)


# Graph will be created lazily on first use
_agent_graph = None

async def get_agent_graph():
    """Get or create the agent graph (async)."""
    global _agent_graph
    if _agent_graph is None:
        _agent_graph = await create_graph()
    return _agent_graph
