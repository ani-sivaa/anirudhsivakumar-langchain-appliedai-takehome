#!/usr/bin/env python
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.tools.memory import get_memory_store, get_memory_stats
from agent.tools.sqlite_store import SQLiteStore


def main():
    print("🧠 Long-Term Memory Inspector\n")
    
    stats = get_memory_stats()
    print("📊 Memory Store Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()
    
    store = get_memory_store()
    
    if not isinstance(store, SQLiteStore):
        print("⚠️  Using in-memory store. No persistent data to show.")
        print("💡 Set MEMORY_STORE=sqlite to enable persistence")
        return
    
    namespaces = store.list_namespaces()
    
    if not namespaces:
        print("📭 No memories stored yet")
        return
    
    print(f"📂 Found {len(namespaces)} namespace(s):\n")
    
    for ns in namespaces:
        print(f"🗂️  Namespace: {' → '.join(ns)}")
        results = store.search(ns)
        
        if results:
            for item in results:
                key = item["key"]
                value = item["value"]
                print(f"   • {key}: {value}")
        else:
            print("   (empty)")
        print()


if __name__ == "__main__":
    main()

