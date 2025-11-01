from typing import Optional


def should_resume(state) -> bool:
    """
    Check if we should resume from an interrupted checkpoint.
    Returns True if there are pending nodes to execute.
    """
    if hasattr(state, 'next') and state.next:
        return len(state.next) > 0
    return False


def get_resume_info(state) -> Optional[str]:
    """Get information about what was interrupted."""
    if hasattr(state, 'next') and state.next:
        pending = ", ".join(state.next)
        return f"Resuming: {pending} pending"
    return None

