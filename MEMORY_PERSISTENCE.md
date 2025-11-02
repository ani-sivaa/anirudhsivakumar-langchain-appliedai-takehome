# Long-Term Memory with SQLite Persistence

## Overview

The agent now supports **persistent long-term memory** using SQLite, allowing facts and preferences to survive restarts.

## Features

- 🗄️ **SQLite-backed storage** - Facts persist across agent restarts
- 🔄 **Automatic fallback** - Defaults to SQLite, falls back to in-memory
- 🔍 **Easy inspection** - View stored memories with included script
- 📊 **Stats tracking** - Monitor memory usage and namespaces
- 🧹 **Namespace isolation** - Separate memories by user/project

## Configuration

### Environment Variables

```bash
# Storage type (default: sqlite)
export MEMORY_STORE=sqlite        # Use SQLite persistence
export MEMORY_STORE=memory        # Use in-memory (testing only)

# Database path (default: ./data/long_term_memory.db)
export MEMORY_DB_PATH=./data/long_term_memory.db
```

### Default Behavior

By default, the agent uses **SQLite persistence** with the database stored at `./data/long_term_memory.db`.

## Usage Examples

### Saving Facts

```bash
> remember my name is John
💾 Saved memory: name

> remember I prefer Python over JavaScript
💾 Saved memory: language_preference
```

### Recalling Facts

```bash
> what's my name?
Found memory 'name': {'name': 'John'}

> what language do I prefer?
Found memory 'language_preference': {'preference': 'Python'}
```

### Persistence Across Restarts

```bash
# Session 1
> remember my favorite color is blue
💾 Saved memory: favorite_color

# *restart agent*

# Session 2
> what's my favorite color?
Found memory 'favorite_color': {'color': 'blue'}  ← Still there!
```

## Inspecting Stored Memories

Use the included inspection script:

```bash
python scripts/inspect_memory.py
```

Output:
```
🧠 Long-Term Memory Inspector

📊 Memory Store Stats:
  db_path: ./data/long_term_memory.db
  total_entries: 5
  total_namespaces: 2
  persistent: True

📂 Found 2 namespace(s):

🗂️  Namespace: users → default_user
   • name: {'name': 'John'}
   • favorite_color: {'color': 'blue'}
   • language_preference: {'preference': 'Python'}
```

## How It Works

### Architecture

1. **Store Interface**: `SQLiteStore` class provides CRUD operations
2. **Memory API**: `agent/tools/memory.py` handles both SQLite and in-memory stores
3. **Persistence Layer**: SQLite database with automatic schema creation
4. **Namespace Model**: Memories organized by `(category, user_id)` tuples

### Database Schema

```sql
CREATE TABLE memory_store (
    namespace TEXT NOT NULL,        -- JSON-encoded tuple: ["users", "alice"]
    key TEXT NOT NULL,              -- Memory key: "name", "preferences"
    value TEXT NOT NULL,            -- JSON-encoded value dict
    created_at TIMESTAMP,           -- When first created
    updated_at TIMESTAMP,           -- When last updated
    PRIMARY KEY (namespace, key)
);
```

### Namespace Structure

```python
# User-specific memories
namespace = ("users", "alice")
store.put(namespace, "name", {"name": "Alice"})

# Project-specific memories  
namespace = ("projects", "my_app")
store.put(namespace, "stack", {"backend": "Python", "frontend": "React"})
```

## API Reference

### SQLiteStore

```python
from agent.tools.sqlite_store import SQLiteStore

store = SQLiteStore("./data/memory.db")

# Save memory
store.put(("users", "alice"), "name", {"name": "Alice"})

# Retrieve memory
value = store.get(("users", "alice"), "name")

# Search namespace
results = store.search(("users", "alice"))

# Delete memory
store.delete(("users", "alice"), "name")

# Clear entire namespace
store.clear_namespace(("users", "alice"))

# Get statistics
stats = store.get_stats()
```

### Memory Helper Functions

```python
from agent.tools.memory import save_memory, get_memory, search_memories, get_memory_stats

# Save
save_memory(("users", "alice"), "name", {"name": "Alice"})

# Retrieve
data = get_memory(("users", "alice"), "name")

# Search
memories = search_memories(("users", "alice"))

# Stats
stats = get_memory_stats()
```

## Testing

Run the memory tests:

```bash
pytest tests/test_sqlite_memory.py -v
```

Tests cover:
- ✅ Basic CRUD operations
- ✅ Updates and overwrites
- ✅ Multiple namespaces
- ✅ Persistence across instances
- ✅ Search and filtering
- ✅ Statistics tracking
- ✅ Namespace clearing

## Comparison: SQLite vs In-Memory

| Feature | SQLite | In-Memory |
|---------|--------|-----------|
| **Persistence** | ✅ Survives restarts | ❌ Lost on restart |
| **Performance** | ~1ms per operation | <0.1ms per operation |
| **Multi-instance** | ✅ Shared across processes | ❌ Isolated per process |
| **Storage** | Disk-based | RAM-based |
| **Use case** | Production | Testing/Dev |

## Performance

- **Write**: ~1-2ms per save
- **Read**: ~0.5-1ms per retrieve  
- **Search**: ~2-5ms per namespace (100 entries)
- **Startup**: ~5ms (database initialization)

## Troubleshooting

### "No such table: memory_store"

The database is auto-created on first use. If you see this error, ensure the `data/` directory is writable.

### "Database is locked"

SQLite is single-writer. If multiple agent instances are running, they may conflict. Use separate database files or switch to PostgreSQL for multi-instance deployments.

### Memory not persisting

Check that `MEMORY_STORE=sqlite` (or unset, as it's the default). If set to `memory`, persistence is disabled.

## Migration from In-Memory

If you have existing code using `InMemoryStore`, no changes needed! The API is compatible:

```python
# Old code (still works)
from agent.tools.memory import get_memory_store
store = get_memory_store()  # Now returns SQLiteStore by default

# New explicit usage
from agent.tools.sqlite_store import SQLiteStore
store = SQLiteStore()
```

## Future Enhancements

Potential improvements:
- PostgreSQL backend for distributed systems
- Full-text search on memory values
- Memory expiration (TTL)
- Memory categories and tags
- Export/import functionality
- Memory compression for large values

