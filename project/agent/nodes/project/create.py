import os
from pathlib import Path
from typing import Dict
from datetime import datetime

from agent.state import AgentState
from agent.tools.llm.wrapper import get_llm
from agent.tools.validation.syntax import validate_python_syntax, should_validate_syntax

WORKSPACE_ROOT = Path.cwd()
PROJECT_FOLDER = WORKSPACE_ROOT / "project"
AGENT_GENERATED_CODE_FOLDER = WORKSPACE_ROOT / "agent-generated-code"


async def create_project_file(state: AgentState) -> Dict:
    """
    Create a single file as part of a project.
    This node runs in parallel for each file.
    Uses async LLM calls for true parallel execution without blocking.
    All files are created within the agent-generated-code folder.
    """
    file_path = state.get("file_path", "")
    file_description = state.get("file_description", "")
    
    # Timing instrumentation with nice formatting
    start_time = datetime.now()
    start_timestamp = start_time.strftime("%H:%M:%S.%f")[:-3]
    print(f"  [PARALLEL] Starting: {file_path} @ {start_timestamp}", flush=True)
    
    if not file_path or not file_description:
        return {"error": "Missing file path or description"}
    
    # Ensure file_path is relative and prepend agent-generated-code if needed
    resolved_path = Path(file_path).resolve()
    
    # Block creating files within the project folder
    try:
        resolved_path.relative_to(PROJECT_FOLDER)
        return {
            "project_results": [f"FAIL: {file_path} - Access denied: Cannot create files within the project folder"],
            "error": "The agent cannot create files within the project folder"
        }
    except ValueError:
        # Path is not within project folder, which is good
        pass
    
    # Ensure path is within agent-generated-code folder
    try:
        resolved_path.relative_to(AGENT_GENERATED_CODE_FOLDER)
        # Path is already within agent-generated-code, convert to relative path
        final_path = str(resolved_path.relative_to(WORKSPACE_ROOT))
    except ValueError:
        # Path is not within agent-generated-code, prepend it
        # If file_path is already absolute, extract just the relative part
        if Path(file_path).is_absolute():
            # Extract just the filename
            final_path = f"agent-generated-code/{Path(file_path).name}"
        else:
            # Prepend agent-generated-code to relative path
            final_path = f"agent-generated-code/{file_path}"
    
    # Update file_path to the final relative path
    file_path = final_path
    
    try:
        llm = get_llm()
        
        system_prompt = """You are a file content generator. Create appropriate content based on the description.

Guidelines:
- Generate complete, working code/content
- Follow best practices for the file type
- Make it production-ready
- No explanations, just the file content"""
        
        user_prompt = f"""Create content for: {file_path}

Description: {file_description}

Generate the complete file content:"""

        # Use async invoke for true parallel execution
        invoke_start = datetime.now()
        content = await llm.ainvoke(prompt=user_prompt, system_prompt=system_prompt)
        invoke_time = (datetime.now() - invoke_start).total_seconds()
        
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines)
        
        if should_validate_syntax(file_path):
            syntax_error = validate_python_syntax(content)
            if syntax_error:
                return {
                    "project_results": [f"FAIL: {file_path} - {syntax_error}"],
                    "error": f"Syntax error in generated file: {syntax_error}"
                }

        # Ensure agent-generated-code folder exists
        AGENT_GENERATED_CODE_FOLDER.mkdir(parents=True, exist_ok=True)
        
        # Convert relative path to absolute for file operations
        if Path(file_path).is_absolute():
            abs_file_path = Path(file_path)
        else:
            abs_file_path = WORKSPACE_ROOT / file_path
        
        abs_file_path = abs_file_path.resolve()
        abs_file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(abs_file_path, "w") as f:
            f.write(content)

        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        end_timestamp = end_time.strftime("%H:%M:%S.%f")[:-3]
        # Use relative path in output
        rel_path = file_path if not Path(file_path).is_absolute() else str(Path(file_path).relative_to(WORKSPACE_ROOT))
        print(f"  [PARALLEL] Completed: {rel_path} @ {end_timestamp} (LLM: {invoke_time:.2f}s, Total: {total_time:.2f}s)", flush=True)

        return {
            "project_results": [f"SUCCESS: {rel_path}"]
        }
        
    except Exception as e:
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        print(f"  [PARALLEL] Failed: {file_path} after {total_time:.2f}s - {str(e)}", flush=True)
        return {
            "project_results": [f"FAIL: {file_path} - {str(e)}"],
            "error": f"Error creating {file_path}: {str(e)}"
        }

