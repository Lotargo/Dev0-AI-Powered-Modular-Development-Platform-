"""
Indexer Script: Indexes the codebase and documentation into Qdrant for RAG.
"""
import os
import sys
import uuid

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from project.core.memory.qdrant_manager import (
    get_qdrant_manager,
    COLLECTION_CODEBASE,
    COLLECTION_DOCUMENTATION
)

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200):
    """
    Splits text into overlapping chunks.
    """
    if not text:
        return []

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks

def index_file(qm, filepath: str, collection: str, chunk_size: int = 1000):
    """
    Reads a file, chunks it, and indexes it into Qdrant.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Skipping {filepath}: {e}")
        return

    chunks = chunk_text(content, chunk_size=chunk_size)
    rel_path = os.path.relpath(filepath, os.getcwd())

    print(f"Indexing {rel_path} ({len(chunks)} chunks)...")

    for i, chunk in enumerate(chunks):
        # Create metadata
        metadata = {
            "filepath": rel_path,
            "filename": os.path.basename(filepath),
            "chunk_index": i,
            "total_chunks": len(chunks)
        }

        # Create unique ID for chunk
        chunk_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{rel_path}_{i}"))

        qm.add_item(
            collection_name=collection,
            text=chunk,
            metadata=metadata,
            item_id=chunk_id
        )

def index_directory(qm, root_dir: str, collection: str, extensions: list):
    """
    Recursively indexes a directory.
    """
    if not os.path.exists(root_dir):
        print(f"Directory not found: {root_dir}")
        return

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip __pycache__ and other hidden dirs
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d != "__pycache__"]

        for filename in filenames:
            if any(filename.endswith(ext) for ext in extensions):
                filepath = os.path.join(dirpath, filename)
                index_file(qm, filepath, collection)

def main():
    qm = get_qdrant_manager()

    # 1. Clear Collections (Full Refresh)
    print("--- Clearing Collections ---")
    qm.clear_collection(COLLECTION_CODEBASE)
    qm.clear_collection(COLLECTION_DOCUMENTATION)

    # 2. Index Codebase (project/ and tests/)
    print("\n--- Indexing Codebase ---")
    code_extensions = [".py", ".json", ".yaml", ".toml"]
    index_directory(qm, "project", COLLECTION_CODEBASE, code_extensions)
    index_directory(qm, "tests", COLLECTION_CODEBASE, [".py"])

    # 3. Index Documentation (dev_docs/ and README.md)
    print("\n--- Indexing Documentation ---")
    index_directory(qm, "dev_docs", COLLECTION_DOCUMENTATION, [".md"])

    if os.path.exists("README.md"):
        index_file(qm, "README.md", COLLECTION_DOCUMENTATION)

    print("\n--- Indexing Complete ---")

if __name__ == "__main__":
    main()
