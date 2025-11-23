from typing import Dict

from agent.state import AgentState
from agent.tools.llm.wrapper import get_llm
from agent.tools.validation.syntax import validate_python_syntax, should_validate_syntax
from agent.tools.code.generation_chain import generate_code_with_review
from agent.constants import ENABLE_CODE_REVIEW


async def modify_code(state: AgentState) -> Dict:
    """
    Uses LLM to modify file content based on user's instruction.
    If the instruction mentions "from conversation", it looks at chat history.
    Otherwise it just shows the current file + instruction to the LLM.
    Checks syntax for Python files before returning.
    """
    content = state.get("content", "")
    instruction = state.get("edit_instruction", "")
    path = state.get("path", "")
    messages = state.get("messages", [])
    
    if not path:
        return {"error": "No file path provided"}
    
    if not instruction:
        return {"error": "No edit instruction provided"}
    
    try:
        llm = get_llm()
        
        if any(phrase in instruction.lower() for phrase in ["previous conversation", "from conversation", "from the previous", "recalled", "from memory"]):
            context_lines = []
            if messages:
                recent_messages = messages[-6:] if len(messages) > 6 else messages
                for msg in recent_messages:
                    role = msg.get("role", "user")
                    msg_content = msg.get("content", "")
                    context_lines.append(f"{role}: {msg_content}")
            
            context_str = "\n\n".join(context_lines)
            
            system_prompt = """You are an expert content writer. Create a file based on the conversation context provided."""

            user_prompt = f"""Based on this conversation:

{context_str}

Create content for file: {path}

The user wants you to write the content that was discussed in the conversation. Extract and format that content appropriately.

Provide the complete file content:"""
        else:
            system_prompt = """You are an expert code editor. Modify code according to the user's instructions.

Guidelines:
- Follow the instruction precisely
- Maintain code style and formatting
- Preserve functionality unless asked to change it
- Return ONLY the complete modified code, no explanations or markdown"""

            if content:
                user_prompt = f"""File: {path}

Current content:
```
{content}
```

Instruction: {instruction}

Provide the complete modified file content:"""
            else:
                user_prompt = f"""Create a new file: {path}

Instruction: {instruction}

Provide the complete file content:"""

        # Use generation chain with review if enabled, otherwise use direct LLM call
        if ENABLE_CODE_REVIEW:
            result = await generate_code_with_review(
                prompt=user_prompt,
                system_prompt=system_prompt,
                path=path
            )
            
            modified_content = result.get("code", "")
            review_feedback = result.get("review_feedback", [])
            quality_score = result.get("quality_score", 1.0)
            iterations = result.get("iterations", 1)
            success = result.get("success", True)
            
            if not success:
                error_msg = result.get("syntax_error", "Code generation failed")
                if review_feedback:
                    error_msg += f". Review feedback: {'; '.join(review_feedback)}"
                return {
                    "error": error_msg,
                    "code_review_feedback": review_feedback,
                    "code_generation_iterations": iterations,
                    "code_quality_score": quality_score
                }
            
            return {
                "modified_content": modified_content,
                "error": "",
                "code_review_feedback": review_feedback,
                "code_generation_iterations": iterations,
                "code_quality_score": quality_score
            }
        else:
            # Fallback to original direct LLM call
            modified_content = await llm.ainvoke(prompt=user_prompt, system_prompt=system_prompt)
            
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
                    return {"error": f"Generated code has syntax error: {syntax_error}"}
            
            return {"modified_content": modified_content, "error": ""}
        
    except Exception as e:
        return {"error": f"Error modifying code: {str(e)}"}

