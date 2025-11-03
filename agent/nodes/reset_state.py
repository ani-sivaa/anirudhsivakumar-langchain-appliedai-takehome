"""
State reset node - cleans up accumulated state between user requests.
Prevents response chaining and context pollution.

DESIGN DECISION: Why reset state between requests?
- Reducers (add, merge_dicts) accumulate values within a request
- This is GOOD for parallel nodes ("SUCCESS: file1" + "SUCCESS: file2")
- But BAD across requests (would show "Project created" + "Edited file" + "Current response")
- Solution: Reset accumulated fields, keep conversation history
- Trade-off: Small overhead (one extra node) for clean outputs

DESIGN DECISION: What gets reset vs preserved?
- KEEP: messages (full conversation), user_input, user_id
- CLEAR: response, edit_results, contents, modifications, approvals
- Logic: Keep what's conversational, clear what's operational
"""

from agent.state import AgentState
from typing import Dict


def reset_accumulated_fields(state: AgentState) -> AgentState:
    """
    Resets accumulated fields at the start of each new request.
    
    The `add` reducer on `response` is needed for parallel nodes,
    but we don't want responses to chain across different user requests.
    
    This node runs first, clearing out old accumulated data.
    """
    # Keep these fields (core conversation state)
    keep_fields = {
        'user_input',
        'messages',
        'user_id'
    }
    
    # Reset everything else to prevent pollution
    cleaned_state = {
        'user_input': state.get('user_input'),
        'messages': state.get('messages', []),
        'user_id': state.get('user_id', 'default_user'),
        # Explicitly clear accumulated fields
        'response': '',
        'edit_results': [],
        'review_comments': [],
        'contents': {},
        'modifications': {},
        'retry_count': 0,
        'approval_required': False,
        'approval_response': None
    }
    
    return cleaned_state

