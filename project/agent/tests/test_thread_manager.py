"""Tests for thread management system."""

import pytest
import tempfile
import os
from pathlib import Path
from agent.tools.thread_manager import ThreadManager


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


def test_create_thread(temp_db):
    """Test creating a new thread."""
    tm = ThreadManager(db_path=temp_db)
    
    thread_id = tm.create_thread(thread_name="Test Conversation")
    
    assert thread_id is not None
    assert len(thread_id) == 36  # UUID length
    
    # Verify it was stored
    thread = tm.get_thread_by_id(thread_id)
    assert thread is not None
    assert thread['thread_name'] == "Test Conversation"
    assert thread['message_count'] == 0


def test_auto_generate_name(temp_db):
    """Test auto-generating thread name from message."""
    tm = ThreadManager(db_path=temp_db)
    
    thread_id = tm.create_thread(first_message="Create a website with React")
    
    thread = tm.get_thread_by_id(thread_id)
    assert thread['thread_name'] == "Create a website with React"


def test_auto_generate_name_truncate(temp_db):
    """Test auto-generating name truncates long messages."""
    tm = ThreadManager(db_path=temp_db)
    
    long_message = "This is a very long message that should be truncated to fit in the thread name field properly"
    thread_id = tm.create_thread(first_message=long_message)
    
    thread = tm.get_thread_by_id(thread_id)
    assert len(thread['thread_name']) <= 50
    assert thread['thread_name'].endswith("...")


def test_rename_thread(temp_db):
    """Test renaming a thread."""
    tm = ThreadManager(db_path=temp_db)
    
    thread_id = tm.create_thread(thread_name="Old Name")
    
    success = tm.rename_thread(thread_id, "New Name")
    assert success is True
    
    thread = tm.get_thread_by_id(thread_id)
    assert thread['thread_name'] == "New Name"


def test_list_threads(temp_db):
    """Test listing threads."""
    tm = ThreadManager(db_path=temp_db)
    
    # Create multiple threads
    id1 = tm.create_thread(thread_name="Thread 1")
    id2 = tm.create_thread(thread_name="Thread 2")
    id3 = tm.create_thread(thread_name="Thread 3")
    
    threads = tm.list_threads(limit=10)
    
    assert len(threads) == 3
    # Should be ordered by last_used (most recent first)
    assert threads[0]['thread_id'] == id3
    assert threads[1]['thread_id'] == id2
    assert threads[2]['thread_id'] == id1


def test_update_thread_activity(temp_db):
    """Test updating thread activity."""
    tm = ThreadManager(db_path=temp_db)
    
    thread_id = tm.create_thread(thread_name="Test")
    
    # Initial count
    thread = tm.get_thread_by_id(thread_id)
    assert thread['message_count'] == 0
    
    # Increment
    tm.update_thread_activity(thread_id)
    thread = tm.get_thread_by_id(thread_id)
    assert thread['message_count'] == 1
    
    # Increment again
    tm.update_thread_activity(thread_id)
    thread = tm.get_thread_by_id(thread_id)
    assert thread['message_count'] == 2


def test_get_thread_by_name(temp_db):
    """Test finding thread by name."""
    tm = ThreadManager(db_path=temp_db)
    
    thread_id = tm.create_thread(thread_name="My Special Project")
    
    # Exact match
    thread = tm.get_thread_by_name("My Special Project")
    assert thread is not None
    assert thread['thread_id'] == thread_id
    
    # Partial match
    thread = tm.get_thread_by_name("Special")
    assert thread is not None
    assert thread['thread_id'] == thread_id
    
    # Case insensitive
    thread = tm.get_thread_by_name("special")
    assert thread is not None
    assert thread['thread_id'] == thread_id
    
    # Not found
    thread = tm.get_thread_by_name("Nonexistent")
    assert thread is None


def test_archive_thread(temp_db):
    """Test archiving a thread."""
    tm = ThreadManager(db_path=temp_db)
    
    thread_id = tm.create_thread(thread_name="To Archive")
    
    # Archive it
    success = tm.archive_thread(thread_id)
    assert success is True
    
    # Verify status changed
    thread = tm.get_thread_by_id(thread_id)
    assert thread['status'] == 'archived'
    
    # Should not appear in active list
    active_threads = tm.list_threads(status='active')
    assert len(active_threads) == 0
    
    # But should appear in archived list
    archived_threads = tm.list_threads(status='archived')
    assert len(archived_threads) == 1


def test_delete_thread(temp_db):
    """Test permanently deleting a thread."""
    tm = ThreadManager(db_path=temp_db)
    
    thread_id = tm.create_thread(thread_name="To Delete")
    
    # Delete it
    success = tm.delete_thread(thread_id)
    assert success is True
    
    # Should not be findable
    thread = tm.get_thread_by_id(thread_id)
    assert thread is None


def test_generate_name_edge_cases(temp_db):
    """Test name generation with edge cases."""
    tm = ThreadManager(db_path=temp_db)
    
    # Empty message
    name = tm._generate_name_from_message("")
    assert name == "New Conversation"
    
    # Whitespace only
    name = tm._generate_name_from_message("   ")
    assert name == "New Conversation"
    
    # Lowercase first letter
    name = tm._generate_name_from_message("create a website")
    assert name == "Create a website"

