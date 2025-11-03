import ast
from typing import Optional


def validate_python_syntax(code: str) -> Optional[str]:
    """
    Checks if Python code is syntactically valid using ast.parse.
    Returns None if good, error message if broken.
    """
    try:
        ast.parse(code)
        return None
    except SyntaxError as e:
        return f"Syntax error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return f"Validation error: {str(e)}"


def should_validate_syntax(path: str) -> bool:
    """Only validate Python files."""
    return path.endswith('.py')

