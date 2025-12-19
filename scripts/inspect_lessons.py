import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from project.core.memory.qdrant_manager import get_qdrant_manager, COLLECTION_EXPERIENCES

def main():
    qm = get_qdrant_manager()
    query = "reportlab pdf barcode"
    print(f"Searching experiences for: '{query}'")

    results = qm.search_items(COLLECTION_EXPERIENCES, query, limit=5)

    for i, res in enumerate(results):
        print(f"\n--- Lesson {i+1} ---")
        print(f"Content: {res.get('content')}")
        print(f"Metadata: {res.get('metadata', {})}")

if __name__ == "__main__":
    main()
