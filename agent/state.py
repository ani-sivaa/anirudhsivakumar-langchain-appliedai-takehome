from typing import TypedDict, Annotated, List, Dict
from operator import add


class AgentState(TypedDict, total=False):
    user_input: str
    response: str
    
    messages: Annotated[List[Dict[str, str]], add]
    
    action: str
    
    path: str
    content: str
    edit_instruction: str
    modified_content: str
    
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
    
    approval_required: bool
    approval_request: Dict
    approval_response: str
    
    error: str
