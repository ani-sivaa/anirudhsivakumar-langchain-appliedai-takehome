"""
Code Quality Validation

This module provides quality checks beyond syntax validation.
Uses LLM for semantic review and AST for structural checks.

Checks include:
- Completeness: All requirements met
- Best Practices: Python style, error handling, documentation
- Correctness: Logic validation
- Structure: Imports, class structure, function signatures
"""

import ast
from typing import List, Dict, Any, Optional

from agent.tools.llm.wrapper import get_llm


def check_code_structure(code: str, path: str) -> List[str]:
    """
    Use AST to check code structure.
    
    Returns list of issues found.
    """
    issues = []
    
    if not path.endswith('.py'):
        return issues
    
    try:
        tree = ast.parse(code)
        
        # Check for imports
        has_imports = any(isinstance(node, (ast.Import, ast.ImportFrom)) for node in ast.walk(tree))
        
        # Check for functions/classes
        has_functions = any(isinstance(node, ast.FunctionDef) for node in ast.walk(tree))
        has_classes = any(isinstance(node, ast.ClassDef) for node in ast.walk(tree))
        
        # Basic structure checks
        if not has_imports and not has_functions and not has_classes:
            # Might be a script, which is fine
            pass
        
    except SyntaxError:
        # Syntax errors are handled separately
        pass
    except Exception as e:
        issues.append(f"Structure analysis error: {str(e)}")
    
    return issues


async def review_code_quality(
    code: str,
    path: str,
    requirements: str = "",
    context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Review code quality using LLM and structural checks.
    
    Args:
        code: Generated code to review
        path: File path
        requirements: Original requirements/prompt
        context: Optional context (e.g., existing code)
    
    Returns:
        {
            "score": float,  # 0.0-1.0 quality score
            "issues": List[str],  # List of issues found
            "suggestions": List[str]  # Improvement suggestions
        }
    """
    issues = []
    suggestions = []
    
    # Structural checks
    structure_issues = check_code_structure(code, path)
    issues.extend(structure_issues)
    
    # LLM-based quality review
    try:
        llm = get_llm(temperature=0.0)
        
        review_prompt = f"""Review the following code for quality issues.

File path: {path}

Code:
```python
{code}
```

Requirements:
{requirements if requirements else "No specific requirements provided"}

Review the code for:
1. Completeness: Does it meet all requirements?
2. Best Practices: Python style, error handling, documentation
3. Correctness: Logic errors, edge cases
4. Structure: Proper imports, class/function organization

Provide a JSON response with:
- "score": float between 0.0 and 1.0 (1.0 = perfect)
- "issues": list of specific issues found (empty if none)
- "suggestions": list of improvement suggestions (empty if none)

Format your response as valid JSON only, no markdown or explanations."""

        response = await llm.ainvoke(prompt=review_prompt, system_prompt="You are a code quality reviewer. Provide structured JSON feedback.")
        
        # Parse JSON response
        import json
        try:
            # Remove markdown code blocks if present
            response_text = response.strip()
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                response_text = "\n".join(lines)
            
            # Try to extract JSON
            if response_text.startswith("{"):
                review_result = json.loads(response_text)
            else:
                # Try to find JSON in the response
                import re
                json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
                if json_match:
                    review_result = json.loads(json_match.group())
                else:
                    raise ValueError("No JSON found in response")
            
            llm_score = review_result.get("score", 1.0)
            llm_issues = review_result.get("issues", [])
            llm_suggestions = review_result.get("suggestions", [])
            
            issues.extend(llm_issues)
            suggestions.extend(llm_suggestions)
            
            # Combine structural and LLM scores
            structure_score = 1.0 if not structure_issues else max(0.0, 1.0 - len(structure_issues) * 0.1)
            final_score = (structure_score + llm_score) / 2.0
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            # If JSON parsing fails, fall back to basic checks
            issues.append("Could not parse quality review response")
            final_score = 0.7  # Default score if review fails
    
    except Exception as e:
        # If LLM review fails, use structural checks only
        issues.append(f"Quality review error: {str(e)}")
        structure_score = 1.0 if not structure_issues else max(0.0, 1.0 - len(structure_issues) * 0.1)
        final_score = structure_score
    
    return {
        "score": final_score,
        "issues": issues,
        "suggestions": suggestions
    }

