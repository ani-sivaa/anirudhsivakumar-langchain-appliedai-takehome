"""
Evaluations for code generation quality.
Tests the agent's ability to generate correct, high-quality code.
"""

import os
from pathlib import Path
import ast
import pytest

from agent.graph import agent_graph


TEST_DIR = Path("test_generated")


@pytest.fixture(autouse=True)
def setup_teardown():
    """Create and cleanup test directory for generated files."""
    TEST_DIR.mkdir(exist_ok=True)
    yield
    # Cleanup
    if TEST_DIR.exists():
        import shutil
        shutil.rmtree(TEST_DIR)


def test_generates_valid_python_syntax():
    """Agent should generate syntactically valid Python code."""
    test_file = TEST_DIR / "test_syntax.py"
    
    config = {"configurable": {"thread_id": "test_syntax"}}
    result = agent_graph.invoke({
        "user_input": f"Create {test_file} with a function that adds two numbers"
    }, config)
    
    assert test_file.exists(), f"File not created at {test_file}"
    code = test_file.read_text()
    
    # Should parse without syntax errors
    try:
        ast.parse(code)
    except SyntaxError as e:
        raise AssertionError(f"Generated invalid Python syntax: {e}")
    
    # Should contain a function
    assert "def " in code


def test_follows_specific_instructions():
    """Agent should follow detailed instructions precisely."""
    test_file = TEST_DIR / "calculator.py"
    
    config = {"configurable": {"thread_id": "test_instructions"}}
    result = agent_graph.invoke({
        "user_input": f"Create {test_file} with a Calculator class that has add, subtract, multiply, and divide methods"
    }, config)
    
    assert test_file.exists()
    code = test_file.read_text()
    
    # Should have a Calculator class
    assert "class Calculator" in code
    
    # Should have all 4 methods
    assert "def add" in code
    assert "def subtract" in code
    assert "def multiply" in code
    assert "def divide" in code


def test_handles_edge_cases_in_generation():
    """Agent should handle edge cases like division by zero."""
    test_file = TEST_DIR / "safe_divide.py"
    
    config = {"configurable": {"thread_id": "test_edge_cases"}}
    result = agent_graph.invoke({
        "user_input": f"Create {test_file} with a safe_divide function that handles division by zero"
    }, config)
    
    assert test_file.exists()
    code = test_file.read_text()
    
    # Should have error handling
    assert any(keyword in code for keyword in ["if", "try", "except", "raise"])
    # Should check for zero
    assert "0" in code or "zero" in code.lower()


def test_generates_correct_imports():
    """Agent should include necessary imports."""
    test_file = TEST_DIR / "file_reader.py"
    
    config = {"configurable": {"thread_id": "test_imports"}}
    result = agent_graph.invoke({
        "user_input": f"Create {test_file} with a function that reads a JSON file and returns a dict"
    }, config)
    
    assert test_file.exists()
    code = test_file.read_text()
    
    # Should import json
    assert "import json" in code or "from json" in code
    # Should have a function
    assert "def " in code


def test_multi_file_consistency():
    """When editing multiple files, changes should be consistent."""
    # Create test files
    file1 = TEST_DIR / "module1.py"
    file2 = TEST_DIR / "module2.py"
    file1.write_text("def old_function():\n    pass")
    file2.write_text("def old_function():\n    pass")
    
    config = {"configurable": {"thread_id": "test_consistency"}}
    result = agent_graph.invoke({
        "user_input": f"Add type hints to {file1} and {file2}"
    }, config)
    
    code1 = file1.read_text()
    code2 = file2.read_text()
    
    # Both should have type hints (-> None or similar)
    assert "->" in code1
    assert "->" in code2


def test_preserves_existing_code():
    """When modifying a file, agent should preserve unrelated code."""
    test_file = TEST_DIR / "existing.py"
    original = """def important_function():
    return 42

def another_function():
    return "hello"
"""
    test_file.write_text(original)
    
    config = {"configurable": {"thread_id": "test_preserve"}}
    result = agent_graph.invoke({
        "user_input": f"Add a docstring to important_function in {test_file}"
    }, config)
    
    modified = test_file.read_text()
    
    # Should still have both functions
    assert "def important_function" in modified
    assert "def another_function" in modified
    # Should have added docstring
    assert '"""' in modified or "'''" in modified


def test_code_quality_standards():
    """Generated code should follow basic quality standards."""
    test_file = TEST_DIR / "quality_test.py"
    
    config = {"configurable": {"thread_id": "test_quality"}}
    result = agent_graph.invoke({
        "user_input": f"Create {test_file} with a function to validate email addresses"
    }, config)
    
    assert test_file.exists()
    code = test_file.read_text()
    
    # Should have a function
    assert "def " in code
    # Should handle invalid input somehow
    assert any(keyword in code for keyword in ["if", "return", "raise"])
    # Valid Python syntax
    ast.parse(code)


def test_handles_complex_requirements():
    """Agent should handle multi-step requirements."""
    test_file = TEST_DIR / "complex.py"
    
    config = {"configurable": {"thread_id": "test_complex"}}
    result = agent_graph.invoke({
        "user_input": f"Create {test_file} with: 1) A User class with name and email attributes, 2) A validate method that checks if email contains @, 3) A __str__ method"
    }, config)
    
    assert test_file.exists()
    code = test_file.read_text()
    
    # Should have User class
    assert "class User" in code
    # Should have the three methods/features
    assert "validate" in code or "email" in code
    assert "__str__" in code or "__repr__" in code
    assert "@" in code  # Email validation logic


def test_parallel_generation_quality():
    """Parallel file creation should maintain quality across all files."""
    config = {"configurable": {"thread_id": "test_parallel_quality"}}
    result = agent_graph.invoke({
        "user_input": f"Create 3 files in {TEST_DIR}: math_utils.py with add function, string_utils.py with capitalize function, list_utils.py with sort function"
    }, config)
    
    # All files should exist
    assert (TEST_DIR / "math_utils.py").exists()
    assert (TEST_DIR / "string_utils.py").exists()
    assert (TEST_DIR / "list_utils.py").exists()
    
    # All should have valid syntax
    for filename in ["math_utils.py", "string_utils.py", "list_utils.py"]:
        filepath = TEST_DIR / filename
        code = filepath.read_text()
        ast.parse(code)  # Should not raise
        assert "def " in code  # Should have a function


def test_error_handling_in_generated_code():
    """Generated code should include appropriate error handling."""
    test_file = TEST_DIR / "file_operations.py"
    
    config = {"configurable": {"thread_id": "test_error_handling"}}
    result = agent_graph.invoke({
        "user_input": f"Create {test_file} with a function that reads a file and handles FileNotFoundError"
    }, config)
    
    assert test_file.exists()
    code = test_file.read_text()
    
    # Should have error handling
    assert "try" in code or "except" in code or "FileNotFoundError" in code
    # Should open/read a file
    assert "open" in code or "read" in code


def test_modification_preserves_functionality():
    """Modifications should not break existing functionality."""
    test_file = TEST_DIR / "working_code.py"
    original = """def process_data(items):
    results = []
    for item in items:
        results.append(item * 2)
    return results
"""
    test_file.write_text(original)
    
    config = {"configurable": {"thread_id": "test_functionality"}}
    result = agent_graph.invoke({
        "user_input": f"Add type hints to {test_file}"
    }, config)
    
    modified = test_file.read_text()
    
    # Should still have the core logic
    assert "for item in items" in modified
    assert "results.append" in modified
    assert "return results" in modified
    # Should have type hints
    assert "->" in modified or "List" in modified or "list" in modified


def test_respects_code_style():
    """Generated code should follow Python conventions."""
    test_file = TEST_DIR / "styled_code.py"
    
    config = {"configurable": {"thread_id": "test_style"}}
    result = agent_graph.invoke({
        "user_input": f"Create {test_file} with a class following Python naming conventions"
    }, config)
    
    assert test_file.exists()
    code = test_file.read_text()
    
    # Should use PascalCase for classes
    lines = code.split("\n")
    class_lines = [l for l in lines if l.strip().startswith("class ")]
    if class_lines:
        # Class name should start with uppercase
        assert any(c.isupper() for c in class_lines[0] if c.isalpha())

