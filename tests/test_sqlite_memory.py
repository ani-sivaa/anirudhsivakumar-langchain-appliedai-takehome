import os
import shutil
from agent.tools.sqlite_store import SQLiteStore


def test_sqlite_store_put_and_get():
    test_db = "./test_data/test_memory.db"
    os.makedirs("./test_data", exist_ok=True)
    
    try:
        store = SQLiteStore(test_db)
        
        namespace = ("users", "test_user")
        key = "name"
        value = {"name": "Alice", "age": 30}
        
        store.put(namespace, key, value)
        result = store.get(namespace, key)
        
        assert result is not None
        assert result["name"] == "Alice"
        assert result["age"] == 30
    finally:
        shutil.rmtree("./test_data", ignore_errors=True)


def test_sqlite_store_update():
    test_db = "./test_data/test_memory.db"
    os.makedirs("./test_data", exist_ok=True)
    
    try:
        store = SQLiteStore(test_db)
        
        namespace = ("users", "test_user")
        key = "preferences"
        
        store.put(namespace, key, {"theme": "dark"})
        store.put(namespace, key, {"theme": "light", "language": "en"})
        
        result = store.get(namespace, key)
        assert result["theme"] == "light"
        assert result["language"] == "en"
    finally:
        shutil.rmtree("./test_data", ignore_errors=True)


def test_sqlite_store_delete():
    test_db = "./test_data/test_memory.db"
    os.makedirs("./test_data", exist_ok=True)
    
    try:
        store = SQLiteStore(test_db)
        
        namespace = ("users", "test_user")
        key = "temp_data"
        
        store.put(namespace, key, {"value": "temporary"})
        assert store.get(namespace, key) is not None
        
        deleted = store.delete(namespace, key)
        assert deleted is True
        assert store.get(namespace, key) is None
        
        deleted_again = store.delete(namespace, key)
        assert deleted_again is False
    finally:
        shutil.rmtree("./test_data", ignore_errors=True)


def test_sqlite_store_search():
    test_db = "./test_data/test_memory.db"
    os.makedirs("./test_data", exist_ok=True)
    
    try:
        store = SQLiteStore(test_db)
        
        namespace = ("projects", "my_project")
        
        store.put(namespace, "stack", {"backend": "Python", "frontend": "React"})
        store.put(namespace, "team", {"size": 5, "remote": True})
        store.put(namespace, "deadline", {"date": "2025-12-31"})
        
        results = store.search(namespace)
        
        assert len(results) == 3
        assert any(r["key"] == "stack" for r in results)
        assert any(r["key"] == "team" for r in results)
        assert any(r["key"] == "deadline" for r in results)
    finally:
        shutil.rmtree("./test_data", ignore_errors=True)


def test_sqlite_store_multiple_namespaces():
    test_db = "./test_data/test_memory.db"
    os.makedirs("./test_data", exist_ok=True)
    
    try:
        store = SQLiteStore(test_db)
        
        ns1 = ("users", "alice")
        ns2 = ("users", "bob")
        
        store.put(ns1, "name", {"name": "Alice"})
        store.put(ns2, "name", {"name": "Bob"})
        
        alice_data = store.get(ns1, "name")
        bob_data = store.get(ns2, "name")
        
        assert alice_data["name"] == "Alice"
        assert bob_data["name"] == "Bob"
        
        alice_results = store.search(ns1)
        bob_results = store.search(ns2)
        
        assert len(alice_results) == 1
        assert len(bob_results) == 1
    finally:
        shutil.rmtree("./test_data", ignore_errors=True)


def test_sqlite_store_persistence():
    test_db = "./test_data/test_memory.db"
    os.makedirs("./test_data", exist_ok=True)
    
    try:
        store1 = SQLiteStore(test_db)
        namespace = ("users", "persistent_user")
        store1.put(namespace, "data", {"persisted": True})
        
        del store1
        
        store2 = SQLiteStore(test_db)
        result = store2.get(namespace, "data")
        
        assert result is not None
        assert result["persisted"] is True
    finally:
        shutil.rmtree("./test_data", ignore_errors=True)


def test_sqlite_store_stats():
    test_db = "./test_data/test_memory.db"
    os.makedirs("./test_data", exist_ok=True)
    
    try:
        store = SQLiteStore(test_db)
        
        store.put(("users", "alice"), "pref1", {"value": 1})
        store.put(("users", "alice"), "pref2", {"value": 2})
        store.put(("users", "bob"), "pref1", {"value": 3})
        
        stats = store.get_stats()
        
        assert stats["total_entries"] == 3
        assert stats["total_namespaces"] == 2
        assert stats["persistent"] is True
        assert test_db in stats["db_path"]
    finally:
        shutil.rmtree("./test_data", ignore_errors=True)


def test_sqlite_store_clear_namespace():
    test_db = "./test_data/test_memory.db"
    os.makedirs("./test_data", exist_ok=True)
    
    try:
        store = SQLiteStore(test_db)
        
        ns1 = ("users", "alice")
        ns2 = ("users", "bob")
        
        store.put(ns1, "key1", {"value": 1})
        store.put(ns1, "key2", {"value": 2})
        store.put(ns2, "key1", {"value": 3})
        
        deleted_count = store.clear_namespace(ns1)
        
        assert deleted_count == 2
        assert len(store.search(ns1)) == 0
        assert len(store.search(ns2)) == 1
    finally:
        shutil.rmtree("./test_data", ignore_errors=True)

