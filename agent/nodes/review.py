from typing import Dict

from agent.state import AgentState
from agent.tools.llm import get_llm


def review_file(state: AgentState) -> Dict:
    """
    Reviews one file's changes using LLM.
    When reviewing a PR with multiple files, this runs in parallel for each file.
    The LLM looks for bugs, performance issues, security problems, etc.
    """
    file_path = state.get("file", "")
    diff = state.get("diff", "")
    
    if not file_path or not diff:
        return {"review_comments": ["Error: Missing file or diff"]}
    
    try:
        llm = get_llm(temperature=0.2)
        
        system_prompt = """You are a code reviewer. Analyze diffs and provide feedback.

Focus on:
- Bugs and logic errors
- Performance issues
- Security vulnerabilities
- Best practices
- Missing error handling

Be specific and actionable. If changes look good, say so briefly."""
        
        user_prompt = f"""Review changes to {file_path}:

```diff
{diff}
```

Provide your review:"""
        
        review_text = llm.invoke(prompt=user_prompt, system_prompt=system_prompt)
        comment = f"**{file_path}**\n{review_text.strip()}"
        
        return {"review_comments": [comment]}
        
    except Exception as e:
        return {"review_comments": [f"Error reviewing {file_path}: {str(e)}"]}

