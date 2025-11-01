from typing import Dict, Any
from langgraph.store.memory import InMemoryStore


_store = None


def get_memory_store() -> InMemoryStore:
    global _store
    if _store is None:
        _store = InMemoryStore()
    return _store


def save_memory(namespace: tuple, key: str, value: Dict[str, Any]) -> str:
    store = get_memory_store()
    store.put(namespace, key, value)
    return f"Saved memory: {key}"


def get_memory(namespace: tuple, key: str) -> Dict[str, Any] | None:
    store = get_memory_store()
    item = store.get(namespace, key)
    return item.value if item else None


def search_memories(namespace: tuple, query: str = "", filter: Dict[str, Any] = None) -> list:
    store = get_memory_store()
    items = store.search(namespace, query=query, filter=filter or {})
    return [item.value for item in items]

