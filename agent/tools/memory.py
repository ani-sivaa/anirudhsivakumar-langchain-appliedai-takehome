import os
from typing import Dict, Any, Union
from langgraph.store.memory import InMemoryStore

from agent.tools.sqlite_store import SQLiteStore


_store = None


def get_memory_store() -> Union[InMemoryStore, SQLiteStore]:
    global _store
    if _store is None:
        store_type = os.getenv("MEMORY_STORE", "sqlite").lower()
        
        if store_type == "sqlite":
            db_path = os.getenv("MEMORY_DB_PATH", "./data/long_term_memory.db")
            _store = SQLiteStore(db_path)
        else:
            _store = InMemoryStore()
    
    return _store


def save_memory(namespace: tuple, key: str, value: Dict[str, Any]) -> str:
    store = get_memory_store()
    
    if isinstance(store, InMemoryStore):
        store.put(namespace, key, value)
    else:
        store.put(namespace, key, value)
    
    return f"Saved memory: {key}"


def get_memory(namespace: tuple, key: str) -> Dict[str, Any] | None:
    store = get_memory_store()
    
    if isinstance(store, InMemoryStore):
        item = store.get(namespace, key)
        return item.value if item else None
    else:
        return store.get(namespace, key)


def search_memories(namespace: tuple, query: str = "", filter: Dict[str, Any] = None) -> list:
    store = get_memory_store()
    
    if isinstance(store, InMemoryStore):
        items = store.search(namespace, query=query, filter=filter or {})
        return [item.value for item in items]
    else:
        results = store.search(namespace)
        return [r["value"] for r in results]


def get_memory_stats() -> Dict[str, Any]:
    store = get_memory_store()
    
    if isinstance(store, SQLiteStore):
        return store.get_stats()
    else:
        return {
            "store_type": "in_memory",
            "persistent": False,
            "warning": "Data will be lost on restart. Set MEMORY_STORE=sqlite for persistence."
        }

