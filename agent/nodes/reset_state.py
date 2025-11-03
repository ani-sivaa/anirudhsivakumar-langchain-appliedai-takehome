"""
State reset node - cleans up accumulated state between user requests.
Prevents response chaining and context pollution.
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

