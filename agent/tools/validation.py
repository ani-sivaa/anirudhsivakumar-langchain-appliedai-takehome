import ast
from typing import Optional


def validate_python_syntax(code: str) -> Optional[str]:
    try:
        ast.parse(code)
        return None
    except SyntaxError as e:
        return f"Syntax error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return f"Validation error: {str(e)}"


def should_validate_syntax(path: str) -> bool:
    return path.endswith('.py')

