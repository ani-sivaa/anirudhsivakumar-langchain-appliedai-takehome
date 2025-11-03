import re
import json
from typing import Optional


def extract_json_from_markdown(text: str) -> str:
    """
    Extracts JSON from LLM responses that might wrap it in markdown code blocks.
    Handles cases like ```json {...} ``` or just {...}
    """
    text = text.strip()
    
    json_pattern = r'```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```'
    match = re.search(json_pattern, text, re.DOTALL)
    if match:
        return match.group(1)
    
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    
    if text.endswith("```"):
        text = text[:-3]
    
    return text.strip()


def safe_json_parse(text: str, default: Optional[dict] = None) -> dict:
    """
    Parses JSON with fallback to default if it fails.
    Useful when LLM returns malformed JSON - we can gracefully fallback instead of crashing.
    """
    try:
        cleaned = extract_json_from_markdown(text)
        return json.loads(cleaned)
    except json.JSONDecodeError:
        if default is not None:
            return default
        raise

