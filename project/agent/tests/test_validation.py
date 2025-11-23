from agent.tools.validation.syntax import validate_python_syntax, should_validate_syntax


def test_validate_python_syntax_valid():
    code = """
def hello():
    return "world"
"""
    error = validate_python_syntax(code)
    assert error is None


def test_validate_python_syntax_invalid():
    code = """
def hello()  # Missing colon
    return "world"
"""
    error = validate_python_syntax(code)
    assert error is not None
    assert "Syntax error" in error


def test_validate_python_syntax_indentation_error():
    code = """
def hello():
return "world"  # Wrong indentation
"""
    error = validate_python_syntax(code)
    assert error is not None


def test_should_validate_syntax_python():
    assert should_validate_syntax("file.py") is True
    assert should_validate_syntax("module.py") is True


def test_should_validate_syntax_not_python():
    assert should_validate_syntax("file.txt") is False
    assert should_validate_syntax("README.md") is False
    assert should_validate_syntax("config.json") is False

