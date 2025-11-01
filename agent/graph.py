from langgraph.graph import StateGraph, END, START, Send
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


def fan_out_reviews(state: AgentState):
    diffs = state.get("diffs", [])
    return [Send("review_file", {"file": d["file"], "diff": d["diff"]}) for d in diffs]


def create_graph():
    graph = StateGraph(AgentState)
    
    graph.add_node("determine_intent", determine_intent)
    graph.add_node("chat", chat_response)
    graph.add_node("read_file", read_file)
    graph.add_node("modify_code", modify_code)
    graph.add_node("write_file", write_file)
    graph.add_node("shell", run_shell)
    graph.add_node("get_git_diff", get_git_diff)
    graph.add_node("review_file", review_file)
    graph.add_node("summarize_review", summarize_review)
    
    graph.add_edge(START, "determine_intent")
    
    graph.add_conditional_edges(
        "determine_intent",
        route_action,
        {
            "chat": "chat",
            "read_file": "read_file",
            "shell": "shell",
            "review": "get_git_diff"
        }
    )
    
    graph.add_edge("chat", END)
    graph.add_edge("shell", END)
    
    graph.add_edge("read_file", "modify_code")
    graph.add_edge("modify_code", "write_file")
    graph.add_edge("write_file", END)
    
    graph.add_conditional_edges("get_git_diff", fan_out_reviews, ["review_file"])
    graph.add_edge("review_file", "summarize_review")
    graph.add_edge("summarize_review", END)
    
    memory = MemorySaver()
    return graph.compile(checkpointer=memory)


agent_graph = create_graph()
