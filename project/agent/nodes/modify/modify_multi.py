from typing import Dict
from datetime import datetime
from pathlib import Path

from agent.state import AgentState
from agent.tools.llm.wrapper import get_llm
from agent.tools.validation.syntax import validate_python_syntax, should_validate_syntax


async def modify_code_multi(state: AgentState) -> Dict:
    """
    Modifies one file when doing parallel multi-file edits.
    Same as modify_code but for the parallel workflow.
    Uses async LLM calls for true parallel execution without blocking.
    """
    path = state.get("path", "")
    contents = state.get("contents", {})
    instruction = state.get("edit_instruction", "")
    
    if not path:
        return {"modifications": {}}
    
    if not instruction:
        return {"modifications": {}}
    
    if path not in contents:
        return {"modifications": {}}
    
    content = contents[path]
    
    # Check if content is an error message
    if isinstance(content, str) and content.startswith("ERROR:"):
        # Skip modification for errored files
        return {"modifications": {path: content}}
    
    # Timing for parallel execution visibility
    start_time = datetime.now()
    short_path = Path(path).name if path else ""
    
    try:
        llm = get_llm()
        
        system_prompt = """You are an expert code editor. Modify code according to the user's instructions.

Guidelines:
- Follow the instruction precisely
- Maintain code style and formatting
- Preserve functionality unless asked to change it
- Return ONLY the complete modified code, no explanations or markdown"""

        user_prompt = f"""File: {path}

Current content:
```
{content}
```

Instruction: {instruction}

Provide the complete modified file content:"""

        llm_start = datetime.now()
        modified_content = await llm.ainvoke(prompt=user_prompt, system_prompt=system_prompt)
        llm_time = (datetime.now() - llm_start).total_seconds()
        
        modified_content = modified_content.strip()
        if modified_content.startswith("```"):
            lines = modified_content.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            modified_content = "\n".join(lines)
        
        if should_validate_syntax(path):
            syntax_error = validate_python_syntax(modified_content)
            if syntax_error:
                return {"modifications": {path: f"ERROR: Syntax error - {syntax_error}"}}
        
        total_time = (datetime.now() - start_time).total_seconds()
        print(f"  [PARALLEL] Modified: {short_path} (LLM: {llm_time:.2f}s, Total: {total_time:.2f}s)", flush=True)
        
        return {"modifications": {path: modified_content}}
        
    except Exception as e:
        return {"modifications": {path: f"ERROR: {str(e)}"}}

