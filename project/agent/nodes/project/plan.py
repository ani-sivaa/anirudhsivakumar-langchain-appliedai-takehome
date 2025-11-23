import json
import time
from typing import Dict

from agent.state import AgentState
from agent.tools.llm.wrapper import get_llm
from agent.tools.parsing.json import safe_json_parse


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
- Make descriptions specific and actionable
- If creating a README.md, make the description VERY SPECIFIC about the project's actual purpose, features, and files
- README descriptions should reference what the user actually requested, not generic template content
- For README files, include details like: project name, what it does, key files/modules, usage examples based on the actual request"""
        
        user_prompt = f"""Plan files for this request:
{project_instruction}

Return JSON with all files needed:"""
        
        response = await llm.ainvoke(prompt=user_prompt, system_prompt=system_prompt)
        plan_data = safe_json_parse(response, default={"files": []})
        files = plan_data.get("files", [])
        
        if not files:
            return {"error": "No files planned"}
        
        # Track start time for parallel execution timing
        # Clear accumulated project_results from previous runs
        return {
            "project_files": files,
            "project_start_time": time.time(),
            "project_results": ["__CLEAR__"],  # Clear previous results
            "error": ""
        }
        
    except Exception as e:
        return {"error": f"Error planning project: {str(e)}"}

