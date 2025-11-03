## LangGraph Coding Agent

**Built by Anirudh Sivakumar**

Hey Palash & Brace! This is my take-home project for the LangChain Applied AI role. I built this to show I understand not just how to use LangGraph, but when and why to use each pattern.

## What It Does

A coding agent that can:
- Edit files with natural language instructions
- Chat about code and answer questions  
- Run shell commands safely
- Review PRs in parallel
- Remember facts across sessions (SQLite persistence)
- Create entire projects from scratch

All built on LangGraph's StateGraph with proper architecture patterns.

## Quick Start

```bash
# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Add your OPENAI_API_KEY to the .env file

# Run
python3 -m cli.main
```

## Example Usage

```
> Add type hints to utils.py
→ determine_intent → check_approval → read_file → modify_code → write_file
✓ Successfully wrote to utils.py

> Review this PR
→ determine_intent → check_approval → get_git_diff → [review_file × N] → summarize_review
Review complete! Checked 3 files...

> Remember my name is Anirudh
→ determine_intent → check_approval → save_memory
💾 Saved memory: name

> What's my name?
→ determine_intent → check_approval → recall_memory
Your name is Anirudh!
```

## Architecture Highlights

**LangGraph Patterns Used:**
- Serial Nodes: read → modify → write flow
- Parallel Execution: Multi-file edits with Send()
- Conditional Edges: Intent-based routing
- Reducers: Aggregating parallel results (operator.add, merge_dicts)
- Persistent Checkpointing: SqliteSaver for durable state (survives restarts, enables time travel)
- Interrupts: Human-in-the-loop for dangerous operations
- Long-term Memory: SQLite store for persistent facts

**Security:**
- Path traversal protection (blocks ../../etc/passwd)
- Dangerous command detection (rm -rf, sudo, etc.)
- Human approval for risky operations
- Python syntax validation before writing

**Code Quality:**
- 52 comprehensive tests
- Type hints throughout
- Docstrings on all functions
- Proper error handling with graceful fallbacks
- Retry logic for LLM calls

## Tests

```bash
pytest tests/ -v
# All 52 tests should pass
```

## Project Structure

```
agent/
  state.py         # AgentState with reducers
  graph.py         # StateGraph definition
  nodes/           # Pure functions for each workflow
  tools/           # Reusable utilities
cli/
  main.py          # Interactive REPL with streaming
tests/             # 52 tests covering all features
```

## Why LangGraph?

I chose LangGraph because it gives you explicit control over complex agent workflows. The graph structure makes it easy to see the flow, debug with checkpoints, and add new capabilities without breaking existing ones. Plus the parallel execution with Send() is really elegant for scaling operations across multiple files.


