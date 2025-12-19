import pytest
from project.modules.memory.vector_db import execute, VectorDBInput

@pytest.mark.integration
def test_vector_db_wrapper():
    """
    Verifies the VectorDB atomic module wrapper around QdrantManager.
    """
    # 1. Add
    add_input = VectorDBInput(
        action="add",
        documents=["Wrapper Test Document"],
        metadatas=[{"source": "test"}],
        ids=["wrapper_test_id"]
    )
    res = execute(add_input)
    assert "Success" in res.status

    # 2. Query
    query_input = VectorDBInput(
        action="query",
        query_text="Wrapper Test",
        n_results=1
    )
    res = execute(query_input)
    assert "Success" in res.status
    assert len(res.results) > 0
    assert "Wrapper Test Document" in res.results[0]

if __name__ == "__main__":
    pytest.main(["-v", __file__])
