# LangGraph Coding Agent

**Take-Home Assessment by Anirudh Sivakumar**

A conversational coding agent built with LangGraph. Edits files, runs commands, reviews code, and remembers context across sessions.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Add OPENAI_API_KEY and PINECONE_API_KEY to .env

python3 -m cli.main
```

## What It Does

- **Edit files**: "add type hints to utils.py"
- **Multi-file edits**: Edits multiple files in parallel
- **Run commands**: "run pytest" with auto-install on missing packages
- **Review PRs**: Reviews multiple files in parallel
- **Remember facts**: "remember my name is X" (SQLite)
- **Semantic search**: "how does the graph work?" (Pinecone RAG)
- **Thread management**: Resume conversations, switch between projects with `/list`, `/switch`, `/rename`

## Key Design Decisions

### 1. Why LangGraph?

Needed **branching logic and parallel execution**. Reviewing 10 files: chains = 30s sequential, LangGraph = 3s parallel with `Send()`.

### 2. Three Memory Systems

- **MemorySaver**: Conversation state within session
- **SQLite**: Long-term user facts
- **Pinecone**: Codebase semantic search (RAG)

Each solves a different problem.

### 3. Intent Classification with LLM

Every message goes through `determine_intent`. LLM extracts action, path, and instruction from natural language.

**Why not regex?** Handles flexible phrasing: "can you please edit utils.py?", "maybe add type hints", etc.

### 4. Human Approval for Dangerous Commands

Commands like `rm -rf` interrupt the graph with `interrupt_before=["check_approval"]`. Waits for y/n before executing.

### 5. Auto-Heal Loop

On "ModuleNotFoundError", graph auto-installs package and retries. Uses conditional edges to route through install node.

### 6. Parallel Execution with Send()

Multi-file operations fan out to N parallel nodes. State reducers (`operator.add`, `merge_dicts`) aggregate results.

### 7. Typo Correction

Fuzzy string matching with `difflib.SequenceMatcher`. Auto-corrects if similarity > 75%.

### 8. Syntax Validation

Python files validated with `ast.parse()` before writing. Prevents broken code from LLM errors.

### 9. RAG Over Codebase

Index files as embeddings in Pinecone. Search retrieves top 5 relevant files, LLM generates answer with actual code snippets.

### 10. State Reducers

Parallel nodes need reducers to combine outputs:

```python
contents: Annotated[Dict[str, str], merge_dicts]
edit_results: Annotated[List[str], operator.add]
```

### 11. Thread Management

User-friendly conversation threads with SQLite storage. Resume old conversations, name threads, switch between projects. Solves the UUID problem - every restart used a new random thread_id, losing access to previous checkpoints.

```python
# Before: New random UUID every time
session_id = str(uuid.uuid4())  # Lost forever!

# After: Named threads with selection menu
thread_id, name = show_thread_menu()  # "Create a website"
```

See [THREAD_MANAGEMENT.md](THREAD_MANAGEMENT.md) for details.

## Architecture

```
User Input → determine_intent → check_approval → Route:
  ├─ edit → read → modify → write
  ├─ edit_multi → [read × N] → modify → [write × N] → summarize
  ├─ shell → run → detect_error → (install if needed) → retry
  ├─ review → get_diff → [review × N] → summarize
  ├─ project → plan → [create × N] → summarize
  ├─ remember/recall → SQLite
  ├─ index_codebase/ask_codebase → Pinecone RAG
  └─ chat → LLM
```

## Project Structure

```
agent/
  state.py              # State with reducers
  graph.py              # Graph definition
  nodes/                # Workflow steps
  tools/                # Utilities (LLM, memory, validation)
cli/
  main.py             # Interactive REPL
tests/                # Unit tests
evals/                # Integration tests
```

## Running Tests

```bash
# Unit tests
pytest tests/ -v

# Integration tests (comprehensive eval suite)
pytest evals/ -v

# Run specific eval
pytest evals/test_architecture_core.py -v
```

## Technical Choices

- **Model**: GPT-4o-mini (fast, cheap)
- **Temperature**: 0.0 for classification, 0.3 for generation
- **Embeddings**: text-embedding-ada-002
- **Vector Store**: Pinecone
- **Checkpointing**: MemorySaver

## Why This Works

Every decision point is **explicit**. You can visualize the graph, debug by inspecting state, and add features without breaking existing ones.

Parallel execution and human-in-the-loop are explicit patterns, not hidden abstractions.

---

**Built with**: LangGraph, LangChain, OpenAI, Pinecone, SQLite
