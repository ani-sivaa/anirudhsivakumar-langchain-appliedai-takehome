import os
from pathlib import Path
from agent.nodes.file_ops.read import validate_path


def test_validate_path_normal_file():
    is_valid, error = validate_path("test_file.txt")
    assert is_valid is True
    assert error == ""


def test_validate_path_subdirectory():
    is_valid, error = validate_path("subdir/test_file.txt")
    assert is_valid is True
    assert error == ""


def test_validate_path_traversal_attack():
    is_valid, error = validate_path("../../../etc/passwd")
    assert is_valid is False
    assert "outside workspace" in error


def test_validate_path_absolute_outside():
    is_valid, error = validate_path("/etc/passwd")
    assert is_valid is False
    assert "outside workspace" in error


def test_validate_path_symlink_escape():
    workspace = Path.cwd()
    test_link = workspace / "escape_link"
    
    try:
        if test_link.exists():
            test_link.unlink()
        
        test_link.symlink_to("/etc/passwd")
        
        is_valid, error = validate_path(str(test_link))
        assert is_valid is False
        assert "outside workspace" in error
    finally:
        if test_link.exists():
            test_link.unlink()

