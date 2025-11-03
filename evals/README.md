# Evaluation Suite

This folder contains comprehensive evaluations for the coding agent's capabilities.

## Quick Start

**Important:** Make sure your virtual environment is activated first!

```bash
# Activate venv (from project root)
source .venv/bin/activate

# Run all code generation quality tests
python -m pytest evals/test_code_generation_quality.py -v

# Run automated dry run (tests all features)
python evals/dry_run_scenarios.py

# View manual evaluation prompts
python evals/eval_prompts.py
```

## What's Being Evaluated

### 1. Code Generation Quality (`test_code_generation_quality.py`)

12 automated tests verifying:
- Generated code has valid Python syntax
- Instructions are followed precisely  
- Edge cases are handled (division by zero, file errors)
- Necessary imports are included
- Multi-file edits maintain consistency
- Existing code is preserved during modifications
- Code follows quality standards (error handling, documentation)
- Complex multi-step requirements work
- Parallel generation maintains quality across all files
- Generated code includes appropriate error handling
- Modifications don't break functionality
- Code follows Python style conventions (PascalCase, snake_case)

### 2. End-to-End Dry Run (`dry_run_scenarios.py`)

Tests all 8 agent workflows:
- **Chat** - Conversational responses
- **Memory** - Save/recall persistent facts
- **Shell** - Safe command execution
- **Single-File Edit** - Create/modify one file
- **Multi-File Edit** - Parallel editing with type hints
- **Project Creation** - Generate multiple related files
- **Code Modification** - Preserve unrelated code while adding features

### 3. Manual Evaluation Prompts (`eval_prompts.py`)

Categorized prompts for manual testing:
- Basic code generation
- Code quality (error handling, validation)
- Multi-file consistency
- Modification accuracy
- Edge case handling
- Complex requirements
- Parallel editing

## Expected Results

### Automated Tests
```bash
$ python -m pytest evals/test_code_generation_quality.py -v
============================= test session starts ==============================
...
============================== 12 passed in 30s ================================
```

### Dry Run
```bash
$ python evals/dry_run_scenarios.py
...
================================================================================
✓ ALL TESTS PASSED (9/9)
================================================================================
```

## Evaluation Criteria

Each generated file should meet these standards:

**Correctness:**
- Valid syntax (passes `ast.parse()`)
- Follows instructions precisely
- Includes all requested features

**Quality:**
- Appropriate error handling
- Necessary imports
- Python naming conventions
- Readable code structure

**Robustness:**
- Handles edge cases (None, empty, invalid)
- Doesn't break on malformed input
- Preserves existing functionality

**Consistency:**
- Multi-file operations apply changes uniformly
- Related files use compatible interfaces
- Consistent style across files

## How to Use

### For Reviewers

1. **Quick validation:**
   ```bash
   python -m pytest evals/test_code_generation_quality.py -v
   ```

2. **Full feature test:**
   ```bash
   python evals/dry_run_scenarios.py
   ```

3. **Manual exploration:**
   ```bash
   python evals/eval_prompts.py  # View prompts
   python -m cli.main            # Run agent interactively
   ```

### For Development

Use these evals during development to ensure changes don't break code generation quality:

```bash
# After making changes to the agent
pytest evals/test_code_generation_quality.py -v
python evals/dry_run_scenarios.py

# If tests fail, investigate and fix
```

## Test Coverage

The evaluation suite covers:
- ✅ Basic functionality (create, edit, chat)
- ✅ Advanced features (parallel, memory, interrupts)
- ✅ Code quality (syntax, imports, error handling)
- ✅ Edge cases (errors, invalid input)
- ✅ Complex scenarios (multi-step, multi-file)
- ✅ Security (path validation, dangerous commands)
- ✅ Consistency (multi-file, style)

