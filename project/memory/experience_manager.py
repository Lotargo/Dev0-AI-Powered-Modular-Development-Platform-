"""
Experience Manager (Query Side of CQRS):
This module is responsible for retrieving enriched experiences (lessons)
from a persistent VectorDB (ChromaDB) to provide context to agents.
"""
import chromadb
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# --- ChromaDB Connection ---
# Use a persistent client to ensure data survives across sessions and can be
# accessed by the background worker.
_chroma_client: Optional[chromadb.Client] = None

def get_chroma_client() -> chromadb.Client:
    """Returns the singleton ChromaDB client instance."""
    global _chroma_client
    if _chroma_client is None:
        # Using a persistent client with a file-based storage.
        # This allows the background worker and the main app to access the same data.
        _chroma_client = chromadb.PersistentClient(path="./project/memory/databases/chroma_db")
    return _chroma_client

# --- Pydantic Models ---
class Input(BaseModel):
    agent_name: str
    task_prompt: str
    k: int = 3  # Number of relevant lessons to retrieve

class Lesson(BaseModel):
    """Represents a lesson learned from a past experience."""
    lesson: str
    source_event: str

class Output(BaseModel):
    lessons: List[Lesson]

# --- Core Logic ---
def execute(input_data: Input) -> Output:
    """
    Retrieves the most relevant lessons for a given agent and task.
    """
    try:
        client = get_chroma_client()

        # Ensure the collection exists, create it if it doesn't
        collection = client.get_or_create_collection(
            name=f"agent_experiences_{input_data.agent_name}"
        )

        # If the collection is empty, there are no lessons to retrieve
        if collection.count() == 0:
            return Output(lessons=[])

        # Query the collection for the most relevant documents
        results = collection.query(
            query_texts=[input_data.task_prompt],
            n_results=min(input_data.k, collection.count()) # Ensure k is not greater than the number of items
        )

        lessons = []
        if results and results['documents']:
            for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
                lessons.append(Lesson(lesson=doc, source_event=metadata.get("source_event", "unknown")))

        return Output(lessons=lessons)
    except Exception as e:
        # In a real system, you'd have more robust error handling and logging
        # For now, return no lessons on failure.
        print(f"Error retrieving lessons from ChromaDB: {e}")
        return Output(lessons=[])
