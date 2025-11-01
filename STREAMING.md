# Streaming Mode with Interrupt & Resume

## Overview

Demonstrates LangGraph's streaming capabilities with checkpoint-based interrupt and resume functionality.

## Features

### 1. Real-time Execution Visibility
Watch each node execute as the agent processes your request:
```
→ determine_intent processing...
→ check_approval processing...
→ chat processing...
  Response: Hello! I was created by...
```

### 2. Interrupt with Ctrl+C
Press Ctrl+C at any time to interrupt execution. The agent saves state at the current checkpoint.

### 3. Automatic Resume
Continue interrupted sessions seamlessly - the agent resumes from the exact checkpoint where it was interrupted.

### 4. State Inspection
View saved checkpoints and conversation history for any session.

## Usage

### Interactive Mode (Streaming is Default)
```bash
# Start the agent (streaming enabled by default)
python -m cli.main
```

### Advanced: Standalone Streaming CLI
```bash
# Single command with streaming
python -m cli.streaming run "Tell me a joke"

# Resume from interrupted session
python -m cli.streaming run "Continue" --thread-id abc-123

# Inspect session state
python -m cli.streaming inspect abc-123

# Interactive mode
python -m cli.streaming interactive
```

## How It Works

### Streaming API
Uses `agent_graph.stream()` with `stream_mode="updates"`:
```python
for event in agent_graph.stream(
    {"user_input": user_input},
    config=config,
    stream_mode="updates"
):
    for node_name, node_data in event.items():
        print(f"→ {node_name}")
```

### Checkpointing
Every node execution creates a checkpoint via `MemorySaver`:
- State persisted after each node
- Can resume from any checkpoint
- Maintains full conversation history

### Interrupt Handling
```python
try:
    for event in agent_graph.stream(...):
        # Process events
except KeyboardInterrupt:
    # State automatically saved!
    state = agent_graph.get_state(config)
    print(f"Saved at checkpoint: {state.config}")
```

## Architecture

```
User Input
    ↓
Streaming Loop:
  [Node 1] → checkpoint → visible update
  [Node 2] → checkpoint → visible update
  [Node 3] → checkpoint → visible update
    ↓
Interrupt (Ctrl+C)?
  Yes → Save checkpoint, exit gracefully
  No → Continue to end
```

## LangGraph Patterns Demonstrated

1. **Streaming Execution** - `stream()` with real-time updates
2. **Checkpointing** - State persistence at every node
3. **Interrupt Handling** - Graceful mid-execution stops
4. **State Inspection** - `get_state()` for checkpoint queries
5. **Session Resume** - Continue from saved checkpoints

## Example Session

```bash
$ python -m cli.main chat --stream

> Tell me about Python

→ determine_intent processing...
→ check_approval processing...
→ chat processing...

Jarvis: Python is a high-level programming language...

^C  # User presses Ctrl+C

⚠ Interrupted! Session saved at checkpoint.
Session ID: abc-123
You can continue this conversation in the next run

# Later...
$ python -m cli.main chat --stream
> What did we just discuss?

Jarvis: We were discussing Python programming language...
```

## Benefits

1. **Transparency** - See exactly what the agent is doing
2. **Control** - Stop anytime without losing work
3. **Debugging** - Inspect state at any checkpoint
4. **Production-ready** - Handles long-running operations safely

