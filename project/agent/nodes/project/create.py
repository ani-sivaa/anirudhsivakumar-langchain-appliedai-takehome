import os
import asyncio
from pathlib import Path
from typing import Dict
from datetime import datetime

from agent.state import AgentState
from agent.tools.llm.wrapper import get_llm
from agent.tools.validation.syntax import validate_python_syntax, should_validate_syntax
from agent.tools.code.generation_chain import generate_code_with_review
from agent.constants import ENABLE_CODE_REVIEW

# Find workspace root by going up from agent code location
# This file is at: project/agent/nodes/project/create.py
# So workspace root is: project/agent/nodes/project/../../../../ = workspace root
# Use resolve() to get absolute path, then go up 5 levels
# Path breakdown: create.py -> project/ -> nodes/ -> agent/ -> project/ -> workspace_root
_THIS_FILE = Path(__file__).resolve()
WORKSPACE_ROOT = _THIS_FILE.parent.parent.parent.parent.parent  # Go up 5 levels to get workspace root
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
        return {"project_results": [f"FAIL: {file_path or 'unknown'} - Missing file path or description"]}
    
    # Normalize the file path - preserve folder structure within agent-generated-code
    # The LLM might return paths like "calculator/main.py" or "calculator_project/src/utils.py"
    # We need to preserve the folder structure and ensure it goes into agent-generated-code/
    
    # Remove any leading slashes or dots, but preserve the folder structure
    normalized_path = file_path.lstrip('/').lstrip('./')
    
    # If path is absolute, try to extract relative part
    if Path(file_path).is_absolute():
        try:
            # Try to make it relative to workspace root
            normalized_path = str(Path(file_path).relative_to(WORKSPACE_ROOT))
        except ValueError:
            # If not relative to workspace, just use the name (fallback)
            normalized_path = Path(file_path).name
    
    # Remove agent-generated-code prefix if already present (avoid duplication)
    if normalized_path.startswith("agent-generated-code/"):
        normalized_path = normalized_path[len("agent-generated-code/"):]
    
    # Always prepend agent-generated-code to ensure files go there
    # This preserves folder structure: "calculator/main.py" -> "agent-generated-code/calculator/main.py"
    final_path = f"agent-generated-code/{normalized_path}"
    
    # Resolve the final path to check it's not in the project folder
    abs_final_path = (WORKSPACE_ROOT / final_path).resolve()
    
    # Block creating files within the project folder
    try:
        abs_final_path.relative_to(PROJECT_FOLDER)
        return {
            "project_results": [f"FAIL: {file_path} - Access denied: Cannot create files within the project folder"]
        }
    except ValueError:
        # Path is not within project folder, which is good
        pass
    
    # Update file_path to the final relative path
    file_path = final_path
    
    try:
        llm = get_llm()

        # Special handling for README files - provide more context
        is_readme = file_path.lower().endswith('readme.md') or 'readme' in file_path.lower()
        project_instruction = state.get("project_instruction", state.get("user_input", ""))

        if is_readme and project_instruction:
            system_prompt = """You are a README file generator. Create a comprehensive, accurate README based on the project description.

Guidelines:
- Write a README that accurately reflects what the user requested
- Include project name, purpose, features, and structure
- Be specific about what this project actually does
- Include usage examples if relevant
- Use proper markdown formatting
- NO generic templates - make it specific to this project
- Base all content on the actual project requirements provided"""

            user_prompt = f"""Create a README for this project:

Project Request: {project_instruction}

File Description: {file_description}

Generate a comprehensive README.md that accurately describes THIS specific project:"""
        else:
            system_prompt = """You are a file content generator. Create appropriate content based on the description.

Guidelines:
- Generate complete, working code/content
- Follow best practices for the file type
- Make it production-ready
- No explanations, just the file content"""

            user_prompt = f"""Create content for: {file_path}

Description: {file_description}

Generate the complete file content:"""

        # Use generation chain with review if enabled, otherwise use direct LLM call
        invoke_start = datetime.now()
        llm_start_timestamp = invoke_start.strftime("%H:%M:%S.%f")[:-3]
        print(f"  [PARALLEL] LLM call starting: {file_path} @ {llm_start_timestamp}", flush=True)
        
        result = None
        iterations = 1
        quality_score = 1.0
        
        if ENABLE_CODE_REVIEW:
            result = await generate_code_with_review(
                prompt=user_prompt,
                system_prompt=system_prompt,
                path=file_path
            )
            
            content = result.get("code", "")
            review_feedback = result.get("review_feedback", [])
            quality_score = result.get("quality_score", 1.0)
            iterations = result.get("iterations", 1)
            success = result.get("success", True)
            
            invoke_time = (datetime.now() - invoke_start).total_seconds()
            
            if not success:
                error_msg = result.get("syntax_error", "Code generation failed")
                if review_feedback:
                    error_msg += f". Review feedback: {'; '.join(review_feedback[:2])}"  # Limit feedback length
                return {
                    "project_results": [f"FAIL: {file_path} - {error_msg}"]
                }
        else:
            # Fallback to original direct LLM call
            # This await is truly async - multiple instances can run concurrently
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
                        "project_results": [f"FAIL: {file_path} - {syntax_error}"]
                    }

        # Ensure agent-generated-code folder exists (async to avoid blocking)
        await asyncio.to_thread(AGENT_GENERATED_CODE_FOLDER.mkdir, parents=True, exist_ok=True)
        
        # Convert relative path to absolute for file operations
        if Path(file_path).is_absolute():
            abs_file_path = Path(file_path)
        else:
            abs_file_path = WORKSPACE_ROOT / file_path
        
        abs_file_path = abs_file_path.resolve()
        # Create parent directories (async to avoid blocking)
        await asyncio.to_thread(abs_file_path.parent.mkdir, parents=True, exist_ok=True)

        # Write file (async to avoid blocking)
        await asyncio.to_thread(abs_file_path.write_text, content, encoding="utf-8")

        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        end_timestamp = end_time.strftime("%H:%M:%S.%f")[:-3]
        # Use relative path in output
        rel_path = file_path if not Path(file_path).is_absolute() else str(Path(file_path).relative_to(WORKSPACE_ROOT))
        
        if ENABLE_CODE_REVIEW and result:
            print(f"  [PARALLEL] Completed: {rel_path} @ {end_timestamp} (LLM: {invoke_time:.2f}s, Iterations: {iterations}, Quality: {quality_score:.2f}, Total: {total_time:.2f}s)", flush=True)
        else:
            print(f"  [PARALLEL] Completed: {rel_path} @ {end_timestamp} (LLM: {invoke_time:.2f}s, Total: {total_time:.2f}s)", flush=True)

        return {
            "project_results": [f"SUCCESS: {rel_path}"],
            "project_file_timings": {rel_path: total_time}
        }
        
    except Exception as e:
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        rel_path = file_path if not Path(file_path).is_absolute() else str(Path(file_path).relative_to(WORKSPACE_ROOT))
        print(f"  [PARALLEL] Failed: {rel_path} after {total_time:.2f}s - {str(e)}", flush=True)
        return {
            "project_results": [f"FAIL: {rel_path} - {str(e)}"],
            "project_file_timings": {rel_path: total_time}
        }

