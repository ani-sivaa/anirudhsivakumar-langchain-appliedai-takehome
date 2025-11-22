import os
import json
from typing import Dict
from datetime import datetime

from agent.state import AgentState
from agent.tools.llm import get_llm
from agent.tools.parsing import safe_json_parse
from agent.tools.validation import validate_python_syntax, should_validate_syntax


async def plan_project(state: AgentState) -> Dict:
    """
    Plan out multiple files for a project using LLM.
    Returns a list of file specs to be created in parallel.
    """
    user_input = state.get("user_input", "")
    project_instruction = state.get("project_instruction", user_input)
    
    try:
        llm = get_llm(temperature=0.3)
        
        system_prompt = """You are a project planner. Given a request, plan out all files needed.

Output valid JSON only with this structure:
{
    "files": [
        {"path": "folder/file1.ext", "description": "what to put in this file"},
        {"path": "folder/file2.ext", "description": "what to put in this file"}
    ]
}

Guidelines:
- Include all necessary files for the request
- Use appropriate file extensions
- Create folder structure as needed
- Make descriptions specific and actionable"""
        
        user_prompt = f"""Plan files for this request:
{project_instruction}

Return JSON with all files needed:"""
        
        response = await llm.ainvoke(prompt=user_prompt, system_prompt=system_prompt)
        plan_data = safe_json_parse(response, default={"files": []})
        files = plan_data.get("files", [])
        
        if not files:
            return {"error": "No files planned"}
        
        return {
            "project_files": files,
            "error": ""
        }
        
    except Exception as e:
        return {"error": f"Error planning project: {str(e)}"}


async def create_project_file(state: AgentState) -> Dict:
    """
    Create a single file as part of a project.
    This node runs in parallel for each file.
    Uses async LLM calls for true parallel execution without blocking.
    """
    file_path = state.get("file_path", "")
    file_description = state.get("file_description", "")
    
    # Timing instrumentation with nice formatting
    start_time = datetime.now()
    start_timestamp = start_time.strftime("%H:%M:%S.%f")[:-3]
    print(f"  [PARALLEL] Starting: {file_path} @ {start_timestamp}", flush=True)
    
    if not file_path or not file_description:
        return {"error": "Missing file path or description"}
    
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

        os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else ".", exist_ok=True)

        with open(file_path, "w") as f:
            f.write(content)

        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        end_timestamp = end_time.strftime("%H:%M:%S.%f")[:-3]
        print(f"  [PARALLEL] Completed: {file_path} @ {end_timestamp} (LLM: {invoke_time:.2f}s, Total: {total_time:.2f}s)", flush=True)

        return {
            "project_results": [f"SUCCESS: {file_path}"]
        }
        
    except Exception as e:
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        print(f"  [PARALLEL] Failed: {file_path} after {total_time:.2f}s - {str(e)}", flush=True)
        return {
            "project_results": [f"FAIL: {file_path} - {str(e)}"],
            "error": f"Error creating {file_path}: {str(e)}"
        }


def collect_project_files(state: AgentState) -> Dict:
    """
    Passthrough node that collects all parallel create_file operations.
    Waits for all file creation nodes to complete before proceeding to summarize.
    """
    return {}


def summarize_project(state: AgentState) -> Dict:
    """
    Summarize project creation results.
    """
    project_results = state.get("project_results", [])
    user_input = state.get("user_input", "")

    success_files = [r for r in project_results if r.startswith("SUCCESS:")]
    failed_files = [r for r in project_results if r.startswith("FAIL:")]

    if not success_files and not failed_files:
        return {
            "response": "No files were created",
            "error": "Project creation failed"
        }

    # Build summary
    summary_lines = []
    if success_files:
        summary_lines.append(f"Project complete! Created {len(success_files)} file(s):")
        summary_lines.extend(success_files)

    if failed_files:
        summary_lines.append(f"\n{len(failed_files)} file(s) failed:")
        summary_lines.extend(failed_files)

    summary = "\n".join(summary_lines)

    return {
        "response": summary,
        "messages": [
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": summary}
        ],
        "error": "Some files failed" if failed_files else ""
    }

