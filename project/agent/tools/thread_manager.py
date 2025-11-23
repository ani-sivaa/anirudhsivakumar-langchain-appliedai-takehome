"""
Thread Manager - User-friendly conversation thread management

Allows users to:
- Resume previous conversations by name or ID
- List all threads with metadata
- Rename threads
- Auto-generate friendly names from conversation content

Uses SQLite to persist thread metadata across sessions.
"""

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any


class ThreadManager:
    """Manages conversation threads with user-friendly names."""
    
    def __init__(self, db_path: str = None):
        """Initialize thread manager with SQLite database."""
        # Use absolute path to ensure it works regardless of current working directory
        if db_path is None:
            # Find project directory (where agent folder is located)
            project_dir = Path(__file__).parent.parent.parent  # tools -> agent -> project/
            db_path = str(project_dir / "data" / "threads.db")
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Create threads table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS threads (
                thread_id TEXT PRIMARY KEY,
                thread_name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_used TEXT NOT NULL,
                message_count INTEGER DEFAULT 0,
                first_message TEXT,
                status TEXT DEFAULT 'active'
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_thread(self, thread_name: Optional[str] = None, first_message: Optional[str] = None) -> str:
        """
        Create a new thread.
        
        Args:
            thread_name: Optional custom name. If not provided, generates from first_message or uses default
            first_message: Optional first user message to generate name from
        
        Returns:
            thread_id: UUID string
        """
        thread_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # Auto-generate name if not provided
        if not thread_name:
            if first_message:
                thread_name = self._generate_name_from_message(first_message)
            else:
                thread_name = f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO threads (thread_id, thread_name, created_at, last_used, message_count, first_message)
            VALUES (?, ?, ?, ?, 0, ?)
        """, (thread_id, thread_name, now, now, first_message))
        
        conn.commit()
        conn.close()
        
        return thread_id
    
    def _generate_name_from_message(self, message: str) -> str:
        """
        Generate a friendly thread name from the first message.
        
        Examples:
            "Create a website" -> "Create a website"
            "Add type hints to utils.py and fix the bug..." -> "Add type hints to utils.py..."
        """
        # Truncate long messages
        if len(message) > 50:
            message = message[:47] + "..."
        
        # Capitalize first letter
        message = message.strip()
        if message:
            message = message[0].upper() + message[1:]
        
        return message or "New Conversation"
    
    def update_thread_activity(self, thread_id: str, message_count: Optional[int] = None):
        """
        Update thread's last_used timestamp and optionally message count.
        
        Args:
            thread_id: Thread to update
            message_count: New message count (increments by 1 if None)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        if message_count is not None:
            cursor.execute("""
                UPDATE threads 
                SET last_used = ?, message_count = ?
                WHERE thread_id = ?
            """, (now, message_count, thread_id))
        else:
            # Increment message count
            cursor.execute("""
                UPDATE threads 
                SET last_used = ?, message_count = message_count + 1
                WHERE thread_id = ?
            """, (now, thread_id))
        
        conn.commit()
        conn.close()
    
    def rename_thread(self, thread_id: str, new_name: str) -> bool:
        """
        Rename a thread.
        
        Args:
            thread_id: Thread to rename
            new_name: New name for the thread
        
        Returns:
            True if successful, False if thread not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE threads 
            SET thread_name = ?
            WHERE thread_id = ?
        """, (new_name, thread_id))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
    
    def get_thread_by_id(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get thread metadata by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT thread_id, thread_name, created_at, last_used, message_count, first_message, status
            FROM threads
            WHERE thread_id = ?
        """, (thread_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "thread_id": row[0],
                "thread_name": row[1],
                "created_at": row[2],
                "last_used": row[3],
                "message_count": row[4],
                "first_message": row[5],
                "status": row[6]
            }
        return None
    
    def get_thread_by_name(self, thread_name: str) -> Optional[Dict[str, Any]]:
        """Get thread metadata by name (case-insensitive partial match)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT thread_id, thread_name, created_at, last_used, message_count, first_message, status
            FROM threads
            WHERE LOWER(thread_name) LIKE LOWER(?)
            ORDER BY last_used DESC
            LIMIT 1
        """, (f"%{thread_name}%",))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "thread_id": row[0],
                "thread_name": row[1],
                "created_at": row[2],
                "last_used": row[3],
                "message_count": row[4],
                "first_message": row[5],
                "status": row[6]
            }
        return None
    
    def list_threads(self, limit: int = 10, status: str = "active") -> List[Dict[str, Any]]:
        """
        List threads ordered by last_used (most recent first).
        
        Args:
            limit: Maximum number of threads to return
            status: Filter by status ('active', 'archived', or 'all')
        
        Returns:
            List of thread metadata dicts
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if status == "all":
            cursor.execute("""
                SELECT thread_id, thread_name, created_at, last_used, message_count, first_message, status
                FROM threads
                ORDER BY last_used DESC
                LIMIT ?
            """, (limit,))
        else:
            cursor.execute("""
                SELECT thread_id, thread_name, created_at, last_used, message_count, first_message, status
                FROM threads
                WHERE status = ?
                ORDER BY last_used DESC
                LIMIT ?
            """, (status, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        threads = []
        for row in rows:
            threads.append({
                "thread_id": row[0],
                "thread_name": row[1],
                "created_at": row[2],
                "last_used": row[3],
                "message_count": row[4],
                "first_message": row[5],
                "status": row[6]
            })
        
        return threads
    
    def archive_thread(self, thread_id: str) -> bool:
        """Archive a thread (soft delete)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE threads 
            SET status = 'archived'
            WHERE thread_id = ?
        """, (thread_id,))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
    
    def delete_thread(self, thread_id: str) -> bool:
        """Permanently delete a thread from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM threads WHERE thread_id = ?", (thread_id,))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0


# Global instance
_thread_manager: Optional[ThreadManager] = None


def get_thread_manager() -> ThreadManager:
    """Get or create the global thread manager instance."""
    global _thread_manager
    if _thread_manager is None:
        _thread_manager = ThreadManager()
    return _thread_manager

