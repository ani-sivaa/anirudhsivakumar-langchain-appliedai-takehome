<<<<<<< HEAD
""" 
Agent graph: this is where i'll define the nodes & edges of the agent.
Some notes:
I am planning to use serial & parallel nodes as well as conditional & reducer edges.
I made this design decision because I want to make the Agent showcase all aspects of the
LangGraph framework.
"""
=======
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver

from agent.state import AgentState
from agent.nodes.intent import determine_intent, route_action
from agent.nodes.chat import chat_response
from agent.nodes.file_io import read_file, write_file
from agent.nodes.modify import modify_code


def create_graph():
    graph = StateGraph(AgentState)
    
    graph.add_node("determine_intent", determine_intent)
    graph.add_node("chat", chat_response)
    graph.add_node("read_file", read_file)
    graph.add_node("modify_code", modify_code)
    graph.add_node("write_file", write_file)
    
    graph.add_edge(START, "determine_intent")
    
    graph.add_conditional_edges(
        "determine_intent",
        route_action,
        {
            "chat": "chat",
            "edit": "read_file",
            "end": END
        }
    )
    
    graph.add_edge("chat", END)
    
    graph.add_edge("read_file", "modify_code")
    graph.add_edge("modify_code", "write_file")
    graph.add_edge("write_file", END)
    
    memory = MemorySaver()
    return graph.compile(checkpointer=memory)


agent_graph = create_graph()
>>>>>>> 9e10a09 (Setup a basic agent for now that has Natural Language File Editing, Conversational Chat capability, Conversation Memory, using LangGraph's memorySaver (persistence capability), Intent Classification like whether or not the user wants to chat or edit files, and Conditional Routing which helps the agent route between chat and edit workflows.)
