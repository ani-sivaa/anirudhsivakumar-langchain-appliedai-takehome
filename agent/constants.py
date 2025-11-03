"""
Constants to avoid magic strings scattered everywhere.
Instead of typing "chat" 20 times, I can now just use Actions.CHAT.
Makes refactoring easier and catches typos at type-check time.
"""


class Actions:
    CHAT = "chat"
    EDIT = "edit"
    EDIT_MULTI = "edit_multi"
    SHELL = "shell"
    REVIEW = "review"
    REMEMBER = "remember"
    RECALL = "recall"
    PROJECT = "project"


class ApprovalStatus:
    APPROVE = "approve"
    DENY = "deny"


class MessageRoles:
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

