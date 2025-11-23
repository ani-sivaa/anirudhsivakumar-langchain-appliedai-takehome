#!/usr/bin/env python3
"""Clear all memory for fresh start"""
import os
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass 

try:
    from pinecone import Pinecone
    HAS_PINECONE = True
except ImportError:
    HAS_PINECONE = False

# Use the same database paths as the agent code
# Data folder is in the project directory
# Find project directory relative to this script
PROJECT_DIR = Path(__file__).parent / "project"
MEMORY_DB_PATH = os.getenv("MEMORY_DB_PATH", str(PROJECT_DIR / "data" / "long_term_memory.db"))
THREADS_DB_PATH = os.getenv("THREADS_DB_PATH", str(PROJECT_DIR / "data" / "threads.db"))
CHECKPOINTS_DB_PATH = os.getenv("CHECKPOINTS_DB_PATH", str(PROJECT_DIR / "data" / "checkpoints.db"))

# Clear SQLite databases
db_files = {
    "long_term_memory.db": MEMORY_DB_PATH,
    "threads.db": THREADS_DB_PATH,
    "checkpoints.db": CHECKPOINTS_DB_PATH,
}

for db_name, db_path in db_files.items():
    db_file = Path(db_path)
    if db_file.exists():
        db_file.unlink()
        print(f"✓ Deleted {db_name} ({db_path})")
    else:
        print(f"  {db_name} not found at {db_path} (already clean)")

# Clear Pinecone namespace
if HAS_PINECONE:
    try:
        api_key = os.getenv("PINECONE_API_KEY")
        if api_key:
            pc = Pinecone(api_key=api_key)
            index_name = os.getenv("PINECONE_INDEX_NAME", "langchain-take-home")
            index = pc.Index(index_name)
            index.delete(delete_all=True, namespace="codebase")
            print("✓ Cleared Pinecone 'codebase' namespace")
        else:
            print("  PINECONE_API_KEY not set, skipping Pinecone cleanup")
    except Exception as e:
        print(f"  Error clearing Pinecone: {e}")
else:
    print("  Pinecone module not available, skipping Pinecone cleanup")

print("\nAll memory cleared! Ready for fresh start.")

