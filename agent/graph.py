from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver

from agent.state import AgentState
from agent.nodes.intent import determine_intent, route_action
from agent.nodes.chat import chat_response
from agent.nodes.file_io import read_file, write_file
from agent.nodes.modify import modify_code
from agent.nodes.shell import run_shell


def create_graph():
    graph = StateGraph(AgentState)
    
    graph.add_node("determine_intent", determine_intent)
    graph.add_node("chat", chat_response)
    graph.add_node("read_file", read_file)
    graph.add_node("modify_code", modify_code)
    graph.add_node("write_file", write_file)
    graph.add_node("shell", run_shell)
    
    graph.add_edge(START, "determine_intent")
    
    graph.add_conditional_edges(
        "determine_intent",
        route_action,
        {
            "chat": "chat",
            "read_file": "read_file",
            "shell": "shell"
        }
    )
    
    graph.add_edge("chat", END)
    graph.add_edge("shell", END)
    
    graph.add_edge("read_file", "modify_code")
    graph.add_edge("modify_code", "write_file")
    graph.add_edge("write_file", END)
    
    memory = MemorySaver()
    return graph.compile(checkpointer=memory)


agent_graph = create_graph()
