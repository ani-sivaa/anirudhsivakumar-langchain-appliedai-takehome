from langgraph.graph import StateGraph, END, START
from langgraph.types import Send
from langgraph.checkpoint.memory import MemorySaver

from agent.state import AgentState
from agent.nodes.intent import determine_intent, route_action
from agent.nodes.chat import chat_response
from agent.nodes.file_io import read_file, write_file
from agent.nodes.modify import modify_code
from agent.nodes.shell import run_shell
from agent.nodes.git import get_git_diff
from agent.nodes.review import review_file
from agent.nodes.summarize import summarize_review
from agent.nodes.memory_ops import save_user_memory, recall_user_memory
from agent.nodes.project import plan_project, create_project_file, summarize_project
from agent.nodes.approval import check_approval_needed, request_approval, route_approval, route_after_approval, handle_denial
from agent.tools.memory import get_memory_store


def fan_out_reviews(state: AgentState):
    diffs = state.get("diffs", [])
    return [Send("review_file", {"file": d["file"], "diff": d["diff"]}) for d in diffs]


def fan_out_project_files(state: AgentState):
    files = state.get("project_files", [])
    return [Send("create_file", {"file_path": f["path"], "file_description": f["description"]}) for f in files]


def create_graph():
    graph = StateGraph(AgentState)
    
    graph.add_node("determine_intent", determine_intent)
    graph.add_node("check_approval", check_approval_needed)
    graph.add_node("request_approval", request_approval)
    graph.add_node("denied", handle_denial)
    graph.add_node("chat", chat_response)
    graph.add_node("read_file", read_file)
    graph.add_node("modify_code", modify_code)
    graph.add_node("write_file", write_file)
    graph.add_node("shell", run_shell)
    graph.add_node("get_git_diff", get_git_diff)
    graph.add_node("review_file", review_file)
    graph.add_node("summarize_review", summarize_review)
    graph.add_node("save_memory", save_user_memory)
    graph.add_node("recall_memory", recall_user_memory)
    graph.add_node("plan_project", plan_project)
    graph.add_node("create_file", create_project_file)
    graph.add_node("summarize_project", summarize_project)
    
    graph.add_edge(START, "determine_intent")
    graph.add_edge("determine_intent", "check_approval")
    
    graph.add_conditional_edges(
        "check_approval",
        route_approval,
        {
            "chat": "chat",
            "shell": "shell",
            "read_file": "read_file",
            "review": "get_git_diff",
            "remember": "save_memory",
            "recall": "recall_memory",
            "project": "plan_project"
        }
    )
    
    graph.add_edge("chat", END)
    graph.add_edge("shell", END)
    graph.add_edge("save_memory", END)
    graph.add_edge("recall_memory", END)
    graph.add_edge("denied", END)
    
    graph.add_edge("read_file", "modify_code")
    graph.add_edge("modify_code", "write_file")
    graph.add_edge("write_file", END)
    
    graph.add_conditional_edges("get_git_diff", fan_out_reviews, ["review_file"])
    graph.add_edge("review_file", "summarize_review")
    graph.add_edge("summarize_review", END)
    
    graph.add_conditional_edges("plan_project", fan_out_project_files, ["create_file"])
    graph.add_edge("create_file", "summarize_project")
    graph.add_edge("summarize_project", END)
    
    checkpointer = MemorySaver()
    store = get_memory_store()
    return graph.compile(checkpointer=checkpointer, store=store)


agent_graph = create_graph()
