#!/usr/bin/env python3
"""
Evaluation prompts to test code generation quality manually.
Copy these into the CLI and verify the results.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

EVAL_PROMPTS = {
    "Basic Code Generation": [
        "Create test_basic.py with a function that reverses a string",
        "Create test_class.py with a Person class that has name and age attributes",
        "Create test_math.py with functions for factorial and fibonacci",
    ],
    
    "Code Quality": [
        "Create test_quality.py with a function to read a JSON file, include proper error handling",
        "Create test_validated.py with a function that validates email addresses using regex",
        "Create test_documented.py with a well-documented API client class",
    ],
    
    "Multi-File Consistency": [
        "Create test_a.py, test_b.py, and test_c.py, each with a hello function",
        "Create model.py with a User class, and service.py with a UserService class that uses the User model",
    ],
    
    "Modification Accuracy": [
        # First create a file
        "Create original.py with a simple add function",
        # Then modify it
        "Add type hints and docstring to the add function in original.py",
        # Verify it preserved the function
    ],
    
    "Edge Cases": [
        "Create safe_math.py with divide function that handles division by zero",
        "Create file_handler.py with read_file function that handles missing files gracefully",
        "Create parser.py with parse_json function that handles malformed JSON",
    ],
    
    "Complex Requirements": [
        "Create rest_api.py with: FastAPI app, /users GET endpoint, /users POST endpoint with validation, error handlers",
        "Create database.py with: SQLAlchemy User model, CRUD operations, connection management",
    ],
    
    "Parallel Editing": [
        # First create files
        "Create file1.py, file2.py, file3.py with simple functions",
        # Then edit them all
        "Add comprehensive docstrings to file1.py, file2.py, and file3.py",
    ],
}


def print_eval_prompts():
    """Print all evaluation prompts."""
    print("="*80)
    print("CODE GENERATION QUALITY EVALUATION PROMPTS")
    print("="*80)
    print("\nCopy these prompts into the agent CLI and verify:")
    print("1. Code runs without syntax errors")
    print("2. Follows the instructions precisely")
    print("3. Includes proper error handling")
    print("4. Maintains consistent style")
    print("\n" + "="*80 + "\n")
    
    for category, prompts in EVAL_PROMPTS.items():
        print(f"\n{category}:")
        print("-" * 40)
        for i, prompt in enumerate(prompts, 1):
            print(f"{i}. {prompt}")
    
    print("\n" + "="*80)
    print("\nAFTER EACH PROMPT:")
    print("- Check if files were created")
    print("- Verify syntax: python -m py_compile <file>")
    print("- Read the code and assess quality")
    print("- Test the functions if possible")
    print("="*80)


if __name__ == "__main__":
    print_eval_prompts()

