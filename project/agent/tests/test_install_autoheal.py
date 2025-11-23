"""
Tests for package installation and auto-heal functionality.
"""

import pytest
from agent.nodes.system.install import (
    install_dependency,
    detect_missing_package,
    should_retry_with_install,
    prepare_retry
)


def test_detect_missing_package_module_not_found():
    """Should detect package name from ModuleNotFoundError."""
    error = "ModuleNotFoundError: No module named 'numpy'"
    assert detect_missing_package(error) == "numpy"


def test_detect_missing_package_import_error():
    """Should detect package name from ImportError."""
    error = "ImportError: No module named 'requests'"
    assert detect_missing_package(error) == "requests"


def test_detect_missing_package_submodule():
    """Should handle submodules correctly."""
    error = "ModuleNotFoundError: No module named 'sklearn.tree'"
    assert detect_missing_package(error) == "scikit-learn"


def test_detect_missing_package_special_mappings():
    """Should map special package names correctly."""
    test_cases = [
        ("ModuleNotFoundError: No module named 'cv2'", "opencv-python"),
        ("ModuleNotFoundError: No module named 'PIL'", "Pillow"),
        ("ModuleNotFoundError: No module named 'yaml'", "pyyaml"),
    ]
    
    for error, expected in test_cases:
        assert detect_missing_package(error) == expected


def test_detect_missing_package_command_not_found():
    """Should detect CLI tool names from command not found errors."""
    error = "pytest: command not found"
    assert detect_missing_package(error) == "pytest"


def test_detect_missing_package_no_match():
    """Should return empty string if no package detected."""
    error = "Some random error message"
    assert detect_missing_package(error) == ""


def test_should_retry_with_install_success():
    """Should not retry if command succeeded."""
    state = {
        "return_code": 0,
        "shell_output": "Success!",
        "retry_count": 0
    }
    assert should_retry_with_install(state) is False


def test_should_retry_with_install_already_retried():
    """Should not retry if already tried once (prevent infinite loops)."""
    state = {
        "return_code": 1,
        "shell_output": "ModuleNotFoundError: No module named 'numpy'",
        "retry_count": 1
    }
    assert should_retry_with_install(state) is False


def test_should_retry_with_install_missing_package():
    """Should retry if command failed with missing package."""
    state = {
        "return_code": 1,
        "shell_output": "ModuleNotFoundError: No module named 'numpy'",
        "retry_count": 0
    }
    assert should_retry_with_install(state) is True


def test_should_retry_with_install_unknown_error():
    """Should not retry if error doesn't suggest missing package."""
    state = {
        "return_code": 1,
        "shell_output": "Syntax error in your code",
        "retry_count": 0
    }
    assert should_retry_with_install(state) is False


def test_prepare_retry():
    """Should prepare state for retry with detected package."""
    state = {
        "shell_output": "ModuleNotFoundError: No module named 'numpy'",
        "command": "python test.py",
        "retry_count": 0
    }
    
    result = prepare_retry(state)
    
    assert result["package_to_install"] == "numpy"
    assert result["retry_count"] == 1
    assert result["original_command"] == "python test.py"


def test_prepare_retry_no_package_detected():
    """Should handle case where no package is detected."""
    state = {
        "shell_output": "Some random error",
        "command": "python test.py",
        "retry_count": 0
    }
    
    result = prepare_retry(state)
    
    assert "error" in result
    assert "couldn't detect missing package" in result["response"]


def test_install_dependency_no_package():
    """Should return error if no package specified."""
    state = {}
    result = install_dependency(state)
    
    assert "error" in result
    assert "No package specified" in result["response"]


def test_install_dependency_extracts_package():
    """Should extract package name from state correctly."""
    state = {"package_to_install": "pytest"}
    
    # Note: This would actually run pip install in a real scenario
    # For testing purposes, we're just checking the state handling
    result = install_dependency(state)
    
    # Should have attempted installation
    assert "return_code" in result
    assert "shell_output" in result

