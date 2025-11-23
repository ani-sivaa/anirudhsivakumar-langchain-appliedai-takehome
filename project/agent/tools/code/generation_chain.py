"""
Code Generation Chain using LangChain LCEL

This module implements a reusable LCEL chain for code generation with review and regeneration.
Uses LangChain's RunnableLambda, RunnableBranch, and RunnablePassthrough for structured workflows.

Architecture:
1. Generate: LLM generates code from prompt
2. Review: LLM reviews code for syntax, quality, and completeness
3. Decide: Determines if regeneration is needed
4. Regenerate: If issues found, generates improved code with feedback

The chain handles retry logic and returns structured feedback.
"""

from typing import Dict, Any, Optional, List

from agent.tools.llm.wrapper import get_llm
from agent.tools.validation.syntax import validate_python_syntax, should_validate_syntax
from agent.tools.validation.quality import review_code_quality
from agent.constants import MAX_CODE_GENERATION_RETRIES, ENABLE_CODE_REVIEW, CODE_QUALITY_THRESHOLD


def clean_code_content(content: str) -> str:
    """Remove markdown code blocks if present."""
    content = content.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines)
    return content


async def generate_code_step(input_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 1: Generate code using LLM.
    
    Input: {
        "prompt": str,
        "system_prompt": str,
        "path": str,
        "iteration": int
    }
    
    Output: {
        "generated_code": str,
        "prompt": str,
        "system_prompt": str,
        "path": str,
        "iteration": int,
        "review_feedback": List[str]
    }
    """
    prompt = input_dict.get("prompt", "")
    system_prompt = input_dict.get("system_prompt", "")
    path = input_dict.get("path", "")
    iteration = input_dict.get("iteration", 0)
    previous_feedback = input_dict.get("review_feedback", [])
    
    llm = get_llm()
    
    # If this is a retry, include previous feedback
    if iteration > 0 and previous_feedback:
        feedback_text = "\n".join([f"- {f}" for f in previous_feedback])
        prompt = f"""{prompt}

Previous attempt had issues. Please address the following feedback:
{feedback_text}

Generate improved code that fixes these issues:"""
    
    # Generate code - this await is truly async, allowing concurrent calls across parallel nodes
    # Multiple instances of this function can run simultaneously without blocking each other
    generated_code = await llm.ainvoke(prompt=prompt, system_prompt=system_prompt)
    generated_code = clean_code_content(generated_code)
    
    return {
        "generated_code": generated_code,
        "prompt": prompt,
        "system_prompt": system_prompt,
        "path": path,
        "iteration": iteration,
        "review_feedback": previous_feedback
    }


async def review_code_step(input_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 2: Review generated code for syntax and quality.
    
    Input: {
        "generated_code": str,
        "path": str,
        "prompt": str,
        "iteration": int,
        "review_feedback": List[str]
    }
    
    Output: {
        "generated_code": str,
        "path": str,
        "prompt": str,
        "iteration": int,
        "review_feedback": List[str],
        "syntax_error": Optional[str],
        "quality_issues": List[str],
        "quality_score": float,
        "needs_regeneration": bool
    }
    """
    generated_code = input_dict.get("generated_code", "")
    path = input_dict.get("path", "")
    prompt = input_dict.get("prompt", "")
    iteration = input_dict.get("iteration", 0)
    
    review_feedback = []
    syntax_error = None
    quality_issues = []
    quality_score = 1.0
    needs_regeneration = False
    
    # Syntax validation
    if should_validate_syntax(path):
        syntax_error = validate_python_syntax(generated_code)
        if syntax_error:
            review_feedback.append(f"Syntax error: {syntax_error}")
            needs_regeneration = True
    
    # Quality review (if enabled and no syntax errors)
    if ENABLE_CODE_REVIEW and not syntax_error:
        quality_result = await review_code_quality(
            code=generated_code,
            path=path,
            requirements=prompt
        )
        quality_issues = quality_result.get("issues", [])
        quality_score = quality_result.get("score", 1.0)
        
        if quality_issues:
            review_feedback.extend(quality_issues)
        
        # Regenerate if quality score is below threshold
        if quality_score < CODE_QUALITY_THRESHOLD:
            needs_regeneration = True
    
    # Don't regenerate if we've hit max retries
    if iteration >= MAX_CODE_GENERATION_RETRIES:
        needs_regeneration = False
    
    return {
        "generated_code": generated_code,
        "path": path,
        "prompt": prompt,
        "system_prompt": input_dict.get("system_prompt", ""),
        "iteration": iteration,
        "review_feedback": review_feedback,
        "syntax_error": syntax_error,
        "quality_issues": quality_issues,
        "quality_score": quality_score,
        "needs_regeneration": needs_regeneration
    }


def decide_regeneration_step(input_dict: Dict[str, Any]) -> str:
    """
    Step 3: Decide whether to regenerate or return final code.
    
    Returns "regenerate" or "finalize"
    """
    needs_regeneration = input_dict.get("needs_regeneration", False)
    iteration = input_dict.get("iteration", 0)
    
    if needs_regeneration and iteration < MAX_CODE_GENERATION_RETRIES:
        return "regenerate"
    return "finalize"


def regenerate_code_step(input_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 4: Regenerate code with feedback.
    
    Increments iteration and loops back to generation.
    """
    iteration = input_dict.get("iteration", 0)
    return {
        **input_dict,
        "iteration": iteration + 1
    }


def finalize_code_step(input_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Final step: Return the code and review information.
    """
    return {
        "code": input_dict.get("generated_code", ""),
        "review_feedback": input_dict.get("review_feedback", []),
        "quality_score": input_dict.get("quality_score", 1.0),
        "iterations": input_dict.get("iteration", 0) + 1,
        "syntax_error": input_dict.get("syntax_error"),
        "success": input_dict.get("syntax_error") is None
    }


# Note: We use a manual retry loop in generate_code_with_review instead of LCEL chains
# because LCEL doesn't support while loops directly. The manual loop gives us better
# control over retry logic and error handling.


async def generate_code_with_review(
    prompt: str,
    system_prompt: str,
    path: str,
    max_retries: Optional[int] = None
) -> Dict[str, Any]:
    """
    Main entry point for code generation with review and regeneration.
    
    Args:
        prompt: User prompt for code generation
        system_prompt: System prompt for LLM
        path: File path (for validation)
        max_retries: Maximum number of regeneration attempts (overrides constant)
    
    Returns:
        {
            "code": str,
            "review_feedback": List[str],
            "quality_score": float,
            "iterations": int,
            "syntax_error": Optional[str],
            "success": bool
        }
    """
    if max_retries is None:
        max_retries = MAX_CODE_GENERATION_RETRIES
    
    initial_input = {
        "prompt": prompt,
        "system_prompt": system_prompt,
        "path": path,
        "iteration": 0,
        "review_feedback": []
    }
    
    # Manual retry loop since LCEL doesn't support while loops
    current_input = initial_input
    for attempt in range(max_retries + 1):
        # Generate
        current_input = await generate_code_step(current_input)
        
        # Review
        current_input = await review_code_step(current_input)
        
        # Check if we need to regenerate
        needs_regeneration = current_input.get("needs_regeneration", False)
        
        if not needs_regeneration:
            # Code is good, finalize
            return finalize_code_step(current_input)
        
        # If we're not at max retries, prepare for next iteration
        if attempt < max_retries:
            current_input["iteration"] = attempt + 1
        else:
            # Max retries reached, return what we have
            return finalize_code_step(current_input)
    
    # Should never reach here, but just in case
    return finalize_code_step(current_input)

