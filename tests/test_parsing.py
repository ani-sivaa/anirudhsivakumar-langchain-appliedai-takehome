from agent.tools.parsing import extract_json_from_markdown, safe_json_parse


def test_extract_json_from_plain_json():
    text = '{"key": "value"}'
    result = extract_json_from_markdown(text)
    assert result == '{"key": "value"}'


def test_extract_json_from_markdown_block():
    text = """```json
{"key": "value"}
```"""
    result = extract_json_from_markdown(text)
    assert result == '{"key": "value"}'


def test_extract_json_from_code_block():
    text = """```
{"key": "value"}
```"""
    result = extract_json_from_markdown(text)
    assert '{"key": "value"}' in result


def test_extract_json_with_extra_text():
    text = """Here is the JSON:
```json
{"key": "value"}
```
That's the result."""
    result = extract_json_from_markdown(text)
    assert result == '{"key": "value"}'


def test_safe_json_parse_valid():
    text = '{"action": "chat"}'
    result = safe_json_parse(text)
    assert result["action"] == "chat"


def test_safe_json_parse_with_markdown():
    text = '```json\n{"action": "edit"}\n```'
    result = safe_json_parse(text)
    assert result["action"] == "edit"


def test_safe_json_parse_invalid_with_default():
    text = 'not valid json'
    result = safe_json_parse(text, default={"action": "chat"})
    assert result["action"] == "chat"


def test_safe_json_parse_invalid_without_default():
    text = 'not valid json'
    try:
        safe_json_parse(text)
        assert False, "Should have raised JSONDecodeError"
    except Exception:
        pass

