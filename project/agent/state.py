from typing import TypedDict, Annotated, List, Dict, Any
from operator import add


def merge_dicts(existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merges dicts from parallel nodes - needed when multiple nodes write to same field.
    When two nodes both add stuff to 'contents', this combines them instead of one overwriting the other.
    """
    if existing is None:
        return new
    if new is None:
        return existing
    return {**existing, **new}


def replace_if_new_else_add(existing: List[str], new: List[str]) -> List[str]:
    """
    Custom reducer for edit_results and project_results.
    - If new list has a special marker "__CLEAR__", replace with empty list
    - If existing is None/empty, use new list
    - Otherwise, concatenate (add behavior)

    This allows us to clear accumulated results when starting a new operation.
    """
    if new and new[0] == "__CLEAR__":
        return []
    if not existing:
        return new
    if not new:
        return existing
    return existing + new


class AgentState(TypedDict, total=False):
    """
    The brain of the agent - stores everything happening during execution.
    total=False means nodes only update fields they care about, not all 40.
    """
    
    # === USER I/O ===
    # What the user sends in and what we send back
    user_input: str  # The user's request: "Add type hints to utils.py"
    response: str  # Our response - each node sets this fresh (no accumulation)
    messages: Annotated[List[Dict[str, str]], add]  # Full chat history: [{role: "user", content: "hi"}]
    
    # === ROUTING ===
    # Determines which workflow to execute
    action: str  # "chat", "edit", "edit_multi", "shell", "project", "remember", "recall"

    # === TASK ORCHESTRATION ===
    # Allows handling multi-step requests in a single invocation
    task_queue: List[Dict[str, Any]]  # Queue of tasks: [{"action": "recall", "memory_key": "name"}, {"action": "project", ...}]
    current_task_index: int  # Which task we're currently executing (0-indexed)
    
    # === SINGLE FILE EDIT (serial: read → modify → write) ===
    path: str  # File path: "agent/state.py"
    content: str  # File content after reading
    edit_instruction: str  # What to change: "Add docstrings"
    modified_content: str  # New content after LLM modifies it
    
    # === MULTI FILE EDIT (parallel: fan-out read/modify/write) ===
    paths: List[str]  # Multiple files: ["a.py", "b.py", "c.py"]
    folder_path: str  # Folder path for discovering files (e.g., "calculator_project")
    contents: Annotated[Dict[str, str], merge_dicts]  # {path: content} - merge_dicts combines from parallel reads
    modifications: Annotated[Dict[str, str], merge_dicts]  # {path: modified_content} - from parallel modifies
    edit_results: Annotated[List[str], replace_if_new_else_add]  # ["✓ a.py", "✓ b.py"] - custom reducer collects results and allows clearing
    project_results: Annotated[List[str], replace_if_new_else_add]  # ["SUCCESS: file.py"] - custom reducer collects results and allows clearing
    edit_file_timings: Annotated[Dict[str, float], merge_dicts]  # {file_path: time_taken} - tracks individual file modification times
    edit_start_time: float  # Timestamp when parallel modification started

    # === SHELL EXECUTION ===
    command: str  # Shell command: "ls -la"
    shell_output: str  # stdout/stderr from command
    return_code: int  # Exit code: 0 = success
    
    # === AUTO-HEAL & INSTALL ===
    package_to_install: str  # Package name for pip install: "numpy"
    retry_count: int  # How many times we've retried (prevent infinite loops)
    original_command: str  # Command to re-run after installing dependency
    
    # === LONG-TERM MEMORY (SQLite persistence) ===
    user_id: str  # User namespace: "default_user"
    memory_key: str  # What to save/recall: "name", "preferences"
    memory_value: Dict  # Data to save: {"name": "Anirudh"}
    memory_query: str  # Search query for memories

    # === CODEBASE SEARCH ===
    codebase_query: str  # Specific question/topic for semantic search: "authentication", "how does the graph work?"
    
    # === PROJECT CREATION (parallel: create multiple files) ===
    project_instruction: str  # High-level goal: "Create a simple website"
    project_files: List[Dict[str, str]]  # [{path: "index.html", description: "..."}]
    file_path: str  # Current file being created in parallel node
    file_description: str  # What content to generate for file
    project_file_timings: Annotated[Dict[str, float], merge_dicts]  # {file_path: time_taken} - tracks individual file creation times
    project_start_time: float  # Timestamp when parallel execution started
    
    # === HUMAN-IN-THE-LOOP (interrupts for dangerous operations) ===
    approval_required: bool  # True if operation needs user approval
    approval_request: Dict  # {type: "command", question: "Run rm -rf?", warning: "Dangerous"}
    approval_response: str  # User's decision: "approve" or "deny"
    
    # === ERROR HANDLING ===
    error: str  # Error message if something fails
    
    # === CODE GENERATION REVIEW ===
    code_review_feedback: Annotated[List[str], add]  # Review comments from each iteration
    code_generation_iterations: int  # Number of generation attempts
    code_quality_score: float  # Quality score (0.0-1.0)
    regeneration_needed: bool  # Whether to retry generation