import os
import json
from typing import Dict

from agent.state import AgentState
from agent.tools.llm import get_llm
from agent.tools.parsing import safe_json_parse
from agent.tools.validation import validate_python_syntax, should_validate_syntax


def plan_project(state: AgentState) -> Dict:
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
        
        response = llm.invoke(prompt=user_prompt, system_prompt=system_prompt)
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


def create_project_file(state: AgentState) -> Dict:
    """
    Create a single file as part of a project.
    This node runs in parallel for each file.
    """
    file_path = state.get("file_path", "")
    file_description = state.get("file_description", "")
    
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
        
        content = llm.invoke(prompt=user_prompt, system_prompt=system_prompt)
        
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
                    "messages": [{"role": "assistant", "content": f"✗ {file_path}: {syntax_error}"}],
                    "error": f"Syntax error in generated file: {syntax_error}"
                }
        
        os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else ".", exist_ok=True)
        
        with open(file_path, "w") as f:
            f.write(content)
        
        return {
            "messages": [{"role": "assistant", "content": f"✓ {file_path}"}]
        }
        
    except Exception as e:
        return {"error": f"Error creating {file_path}: {str(e)}"}


def summarize_project(state: AgentState) -> Dict:
    """
    Summarize project creation results.
    """
    project_files = state.get("project_files", [])
    messages = state.get("messages", [])
    
    created_files = [msg.get("content", "") for msg in messages if msg.get("content", "").startswith("✓")]
    
    if not created_files:
        return {
            "response": "No files were created",
            "error": "Project creation failed"
        }
    
    summary = f"Project complete! Created {len(created_files)} files:\n" + "\n".join(created_files)
    
    return {
        "response": summary,
        "messages": [{"role": "assistant", "content": summary}],
        "error": ""
    }

