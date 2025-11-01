from typing import Dict

from agent.state import AgentState
from agent.tools.llm import get_llm


def summarize_review(state: AgentState) -> Dict:
    review_comments = state.get("review_comments", [])
    
    if not review_comments:
        return {
            "review_summary": "No review comments available.",
            "messages": [{"role": "assistant", "content": "Review complete: No changes to review."}]
        }
    
    if len(review_comments) == 1:
        summary = f"# Code Review\n\n{review_comments[0]}"
        return {
            "review_summary": summary,
            "error": "",
            "messages": [{"role": "assistant", "content": summary}]
        }
    
    try:
        llm = get_llm(temperature=0.1)
        combined_comments = "\n\n---\n\n".join(review_comments)
        
        system_prompt = """You are a senior engineer summarizing code review feedback.

Your task:
- Synthesize per-file reviews into a cohesive summary
- Highlight critical issues
- Group similar feedback across files
- Provide overall assessment
- Keep it concise and actionable"""
        
        user_prompt = f"""Summarize this code review feedback:

{combined_comments}

Provide a structured summary:"""
        
        summary_text = llm.invoke(prompt=user_prompt, system_prompt=system_prompt)
        summary = f"# Code Review Summary\n\n{summary_text.strip()}\n\n---\n\n## File Reviews\n\n{combined_comments}"
        
        return {
            "review_summary": summary,
            "error": "",
            "messages": [{"role": "assistant", "content": summary}]
        }
        
    except Exception as e:
        summary = f"# Code Review\n\n{combined_comments}"
        return {
            "review_summary": summary,
            "error": f"Summary generation failed ({str(e)})",
            "messages": [{"role": "assistant", "content": summary}]
        }

