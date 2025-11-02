from typing import TypedDict, Annotated, List, Dict, Any
from operator import add


def merge_dicts(existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    if existing is None:
        return new
    if new is None:
        return existing
    return {**existing, **new}


class AgentState(TypedDict, total=False):
    user_input: str
    response: Annotated[str, add]
    
    messages: Annotated[List[Dict[str, str]], add]
    
    action: str
    
    path: str
    content: str
    edit_instruction: str
    modified_content: str
    
    paths: List[str]
    contents: Annotated[Dict[str, str], merge_dicts]
    modifications: Annotated[Dict[str, str], merge_dicts]
    edit_results: Annotated[List[str], add]
    
    command: str
    shell_output: str
    return_code: int
    
    base_branch: str
    head_branch: str
    diffs: List[Dict[str, str]]
    file: str
    diff: str
    review_comments: Annotated[List[str], add]
    review_summary: str
    
    user_id: str
    memory_key: str
    memory_value: Dict
    memory_query: str
    
    project_instruction: str
    project_files: List[Dict[str, str]]
    file_path: str
    file_description: str
    
    error: str
