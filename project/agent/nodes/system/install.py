"""
Package installation node - installs Python packages via pip.
Used both for explicit install requests and auto-heal retry logic.
"""

import subprocess
from typing import Dict

from agent.state import AgentState


def install_dependency(state: AgentState) -> AgentState:
    """
    Installs a Python package using pip.
    
    Can be triggered:
    - Explicitly by user: "install numpy"
    - Auto-heal: shell command failed due to missing import, retry after install
    
    Extracts package name from state (either from command or detected from error).
    """
    package = state.get("package_to_install", "")
    
    if not package:
        return {
            **state,
            "response": "No package specified to install",
            "error": "Missing package name"
        }
    
    try:
        # Run pip install
        result = subprocess.run(
            ["pip", "install", package],
            capture_output=True,
            text=True,
            timeout=120  # 2 min timeout for large packages
        )
        
        if result.returncode == 0:
            response = f"Successfully installed {package}"
            if result.stdout:
                response += f"\n\nOutput:\n{result.stdout}"
            
            return {
                **state,
                "response": response,
                "shell_output": result.stdout,
                "return_code": 0,
                "error": None
            }
        else:
            error_msg = result.stderr or result.stdout or "Unknown error"
            return {
                **state,
                "response": f"Failed to install {package}:\n{error_msg}",
                "shell_output": error_msg,
                "return_code": result.returncode,
                "error": error_msg
            }
    
    except subprocess.TimeoutExpired:
        return {
            **state,
            "response": f"Installation of {package} timed out (>2 min)",
            "error": "Installation timeout"
        }
    except Exception as e:
        return {
            **state,
            "response": f"Error installing {package}: {str(e)}",
            "error": str(e)
        }


def detect_missing_package(error_output: str) -> str:
    """
    Analyzes error output to detect missing Python packages.
    Returns the package name to install, or empty string if not detected.
    
    Handles common patterns:
    - ModuleNotFoundError: No module named 'numpy'
    - ImportError: No module named 'requests'
    - Command 'xyz' not found (for CLI tools)
    """
    if not error_output:
        return ""
    
    # Pattern 1: ModuleNotFoundError: No module named 'package'
    if "ModuleNotFoundError" in error_output or "ImportError" in error_output:
        import re
        match = re.search(r"No module named ['\"]([^'\"]+)['\"]", error_output)
        if match:
            module = match.group(1)
            # Handle submodules (e.g., 'sklearn.tree' -> 'scikit-learn')
            package_map = {
                'sklearn': 'scikit-learn',
                'cv2': 'opencv-python',
                'PIL': 'Pillow',
                'yaml': 'pyyaml',
            }
            base_module = module.split('.')[0]
            return package_map.get(base_module, base_module)
    
    # Pattern 2: command not found (for CLI tools like pytest, black, etc.)
    if "command not found" in error_output:
        import re
        match = re.search(r"([a-z0-9_-]+): command not found", error_output)
        if match:
            return match.group(1)
    
    return ""


def should_retry_with_install(state: AgentState) -> bool:
    """
    Determines if we should attempt auto-heal by installing a package.
    
    Criteria:
    - Shell command failed (non-zero return code)
    - Error suggests missing package
    - Haven't retried yet (prevent infinite loops)
    """
    return_code = state.get("return_code", 0)
    error_output = state.get("shell_output", "")
    retry_count = state.get("retry_count", 0)
    
    if return_code == 0:
        return False  # Command succeeded
    
    if retry_count >= 1:
        return False  # Already retried once, don't loop
    
    package = detect_missing_package(error_output)
    return bool(package)


def prepare_retry(state: AgentState) -> AgentState:
    """
    Prepares state for auto-heal retry.
    Detects missing package and sets up for install → retry flow.
    """
    error_output = state.get("shell_output", "")
    package = detect_missing_package(error_output)
    
    if not package:
        return {
            **state,
            "response": f"Command failed but couldn't detect missing package:\n{error_output}",
            "error": "Auto-heal failed - unknown error"
        }
    
    return {
        **state,
        "package_to_install": package,
        "retry_count": state.get("retry_count", 0) + 1,
        "original_command": state.get("command", "")
    }

