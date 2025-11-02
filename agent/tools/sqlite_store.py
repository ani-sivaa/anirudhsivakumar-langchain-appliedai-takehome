import sqlite3
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import contextmanager


class SQLiteStore:
    def __init__(self, db_path: str = "./data/long_term_memory.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_store (
                    namespace TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (namespace, key)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_namespace 
                ON memory_store(namespace)
            """)
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def put(self, namespace: tuple, key: str, value: Dict[str, Any]) -> None:
        namespace_str = json.dumps(namespace)
        value_str = json.dumps(value)
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO memory_store (namespace, key, value, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(namespace, key) 
                DO UPDATE SET 
                    value = excluded.value,
                    updated_at = CURRENT_TIMESTAMP
            """, (namespace_str, key, value_str))
            conn.commit()
    
    def get(self, namespace: tuple, key: str) -> Optional[Dict[str, Any]]:
        namespace_str = json.dumps(namespace)
        
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT value FROM memory_store 
                WHERE namespace = ? AND key = ?
            """, (namespace_str, key))
            row = cursor.fetchone()
            
            if row:
                return json.loads(row['value'])
            return None
    
    def delete(self, namespace: tuple, key: str) -> bool:
        namespace_str = json.dumps(namespace)
        
        with self._get_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM memory_store 
                WHERE namespace = ? AND key = ?
            """, (namespace_str, key))
            conn.commit()
            return cursor.rowcount > 0
    
    def search(self, namespace: tuple) -> List[Dict[str, Any]]:
        namespace_str = json.dumps(namespace)
        
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT key, value FROM memory_store 
                WHERE namespace = ?
                ORDER BY updated_at DESC
            """, (namespace_str,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "key": row['key'],
                    "value": json.loads(row['value'])
                })
            return results
    
    def list_namespaces(self) -> List[tuple]:
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT DISTINCT namespace FROM memory_store
            """)
            return [json.loads(row['namespace']) for row in cursor.fetchall()]
    
    def clear_namespace(self, namespace: tuple) -> int:
        namespace_str = json.dumps(namespace)
        
        with self._get_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM memory_store WHERE namespace = ?
            """, (namespace_str,))
            conn.commit()
            return cursor.rowcount
    
    def get_stats(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_entries,
                    COUNT(DISTINCT namespace) as total_namespaces
                FROM memory_store
            """)
            row = cursor.fetchone()
            
            return {
                "db_path": self.db_path,
                "total_entries": row['total_entries'],
                "total_namespaces": row['total_namespaces'],
                "persistent": True
            }

