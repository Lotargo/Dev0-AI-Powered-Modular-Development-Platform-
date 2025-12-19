"""
Migration Script: Moves data from ChromaDB to Qdrant.
Reads 'dev0_memory' from Chroma and writes to 'experiences' in Qdrant.
"""
import sys
import os
import uuid
import chromadb
from tqdm import tqdm

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from project.core.memory.qdrant_manager import get_qdrant_manager, COLLECTION_EXPERIENCES

CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "dev0_memory"

def migrate():
    print(f"--- Starting Migration from ChromaDB ({CHROMA_PATH}) to Qdrant ---")

    if not os.path.exists(CHROMA_PATH):
        print("No ChromaDB found at path. Skipping migration.")
        return

    # 1. Read from Chroma
    print("Reading from ChromaDB...")
    try:
        chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = chroma_client.get_collection(COLLECTION_NAME)

        # Get all data
        data = collection.get()
        documents = data['documents']
        metadatas = data['metadatas']
        ids = data['ids']

        if not documents:
            print("ChromaDB collection is empty.")
            return

        print(f"Found {len(documents)} documents to migrate.")

    except Exception as e:
        print(f"Error reading from ChromaDB: {e}")
        # If collection doesn't exist, it throws ValueError
        return

    # 2. Write to Qdrant
    print("Writing to Qdrant...")
    qm = get_qdrant_manager()
    qm.ensure_collection(COLLECTION_EXPERIENCES)

    # We reuse the ID from Chroma if possible, but Qdrant likes UUIDs or Ints.
    # Chroma IDs might be strings. Qdrant supports UUID strings.
    # We let QdrantManager re-embed the text.

    # Note: QdrantManager doesn't have a raw 'add_document' method yet, only 'upsert_module'.
    # I need to add a generic 'add_memory' method to QdrantManager or access client directly.
    # Accessing client directly is easier for this script.

    from qdrant_client.http import models

    points = []
    for i, doc in tqdm(enumerate(documents), total=len(documents)):
        meta = metadatas[i] if metadatas else {}
        doc_id = ids[i]

        # Ensure ID is a UUID
        try:
            uuid.UUID(doc_id)
            point_id = doc_id
        except ValueError:
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, doc_id))

        # Embed
        vector = qm._get_embedding(doc)

        # Payload
        payload = {
            "content": doc,
            **meta
        }

        points.append(models.PointStruct(
            id=point_id,
            vector=vector,
            payload=payload
        ))

    # Batch upsert
    qm.client.upsert(
        collection_name=COLLECTION_EXPERIENCES,
        points=points
    )

    print("--- Migration Finished Successfully ---")

if __name__ == "__main__":
    migrate()
