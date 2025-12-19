"""
This script serves as the main entry point for indexing all the building
blocks (modules, adapters, recipes) in the project.
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from project.core.knowledge_base_manager import create_knowledge_base, discover_blocks
from project.core.memory.qdrant_manager import get_qdrant_manager

def main():
    print("--- Starting Module Indexing Process ---")

    # 1. Legacy JSON (Backward Compatibility)
    create_knowledge_base()
    print("--- Legacy JSON Index Updated ---")

    # 2. Qdrant Indexing
    print("--- Indexing to Qdrant (Vector DB) ---")
    try:
        qm = get_qdrant_manager()
        blocks = discover_blocks()

        count = 0
        for block in blocks:
            qm.upsert_module(block)
            count += 1

        print(f"--- Qdrant Indexing Finished: {count} modules indexed ---")
    except Exception as e:
        print(f"--- Qdrant Indexing Failed: {e} ---")

if __name__ == "__main__":
    main()
