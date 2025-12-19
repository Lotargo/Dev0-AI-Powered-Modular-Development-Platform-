import pytest
import shutil
import os
from project.core.memory.qdrant_manager import get_qdrant_manager, COLLECTION_KNOWLEDGE_BASE

@pytest.mark.integration
def test_qdrant_indexing_and_search():
    """
    Verifies that modules can be indexed into Qdrant and retrieved via semantic search.
    """
    qm = get_qdrant_manager()

    # 1. Define a dummy module payload
    dummy_module = {
        "name": "test_file_writer",
        "type": "atomic",
        "import_path": "project.modules.test.writer",
        "description": "Writes text to a file securely.",
        "schemas": {"Input": {}, "Output": {}},
        "metadata": {}
    }

    # 2. Index it
    print("Indexing dummy module...")
    qm.upsert_module(dummy_module)

    # 3. Search for it (Semantic query)
    query = "I need to write data to disk"
    print(f"Searching for: '{query}'")
    results = qm.search_tools(query, limit=1)

    print("Results:", results)

    # 4. Assertions
    assert len(results) > 0, "No results returned from Qdrant"
    found_module = results[0]
    assert found_module["name"] == "test_file_writer", f"Expected 'test_file_writer', got {found_module.get('name')}"
    assert found_module["import_path"] == "project.modules.test.writer"

if __name__ == "__main__":
    pytest.main(["-v", __file__])
