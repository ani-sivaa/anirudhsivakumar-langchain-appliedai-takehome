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

# Clear SQLite databases
data_dir = Path("./data")
if data_dir.exists():
    for db_file in ["long_term_memory.db", "threads.db", "checkpoints.db"]:
        db_path = data_dir / db_file
        if db_path.exists():
            db_path.unlink()
            print(f"✓ Deleted {db_file}")
        else:
            print(f"  {db_file} not found (already clean)")

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

