from typing import Dict

from agent.state import AgentState
from agent.tools.llm.wrapper import get_llm


async def chat_response(state: AgentState) -> Dict:
    """
    Just normal chat - answers questions, says hi, talks about code.
    Passes the whole conversation history to the LLM so it remembers context.
    """
    user_input = state.get("user_input", "")
    messages = state.get("messages", [])
    
    try:
        llm = get_llm(temperature=0.7)
        
        system_prompt = """You are Anicode, a coding assistant created by Anirudh Sivakumar. 

About your creator:
- Anirudh Sivakumar built you to showcase his skills with LangGraph
- He's passionate about AI agents and really wants to work at LangChain
- You were built using LangGraph's node based architecture features: serial nodes, parallel execution, conditional edges, and reducers

Your personality:
- Enthusiastic and friendly
- Proud of your creator's work
- Excited about LangGraph and LangChain technology
- When asked who made you, mention Anirudh Sivakumar and his interest in working at LangChain

Your capabilities:
- Edit files with natural language instructions
- Have conversations about code
- Answer questions
- Remember conversation context

Maintain conversation context and be genuinely helpful while showing personality."""

        conversation_context = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            conversation_context.append(f"{role}: {content}")
        
        conversation_context.append(f"user: {user_input}")
        full_prompt = "\n\n".join(conversation_context)
        
        response_text = await llm.ainvoke(prompt=full_prompt, system_prompt=system_prompt)
        
        return {
            "response": response_text,
            "messages": [
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": response_text}
            ]
        }
        
    except Exception as e:
        return {"response": f"Error: {str(e)}"}

