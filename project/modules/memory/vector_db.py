"""
Atomic module for Vector Database operations (Qdrant).
Replaces ChromaDB with QdrantManager.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from project.core.framework.atomic import atomic
from project.core.memory.qdrant_manager import get_qdrant_manager, COLLECTION_EXPERIENCES

class VectorDBInput(BaseModel):
    action: str = Field(..., description="Action: 'add' or 'query'.")
    collection_name: str = Field("dev0_memory", description="Name of the collection.")
    documents: Optional[List[str]] = Field(None, description="List of text documents to add.")
    metadatas: Optional[List[Dict[str, Any]]] = Field(None, description="Metadata for documents.")
    ids: Optional[List[str]] = Field(None, description="IDs for documents.")
    query_text: Optional[str] = Field(None, description="Text to query.")
    n_results: int = Field(3, description="Number of results to return.")

class VectorDBOutput(BaseModel):
    status: str
    results: Optional[List[str]] = None
    metadatas: Optional[List[Dict[str, Any]]] = None

@atomic
def execute(input_data: VectorDBInput) -> VectorDBOutput:
    """
    Performs operations on the Vector Database (Qdrant).
    """
    try:
        qm = get_qdrant_manager()

        # Map legacy collection name to Qdrant constant
        collection = input_data.collection_name
        if collection == "dev0_memory":
            collection = COLLECTION_EXPERIENCES

        if input_data.action == "add":
            if not input_data.documents or not input_data.ids:
                 return VectorDBOutput(status="Error: 'documents' and 'ids' required for add.")

            docs = input_data.documents
            metas = input_data.metadatas or [{} for _ in docs]
            ids = input_data.ids

            if len(docs) != len(ids):
                return VectorDBOutput(status="Error: Mismatch length between documents and ids.")

            for i in range(len(docs)):
                # Ensure metadata list matches documents list
                meta = metas[i] if i < len(metas) else {}
                qm.add_item(
                    collection_name=collection,
                    text=docs[i],
                    metadata=meta,
                    item_id=ids[i]
                )
            return VectorDBOutput(status="Success: Added documents to Qdrant.")

        elif input_data.action == "query":
            if not input_data.query_text:
                 return VectorDBOutput(status="Error: 'query_text' required for query.")

            payloads = qm.search_items(
                collection_name=collection,
                query=input_data.query_text,
                limit=input_data.n_results
            )

            # Format output to match legacy Chroma structure
            # Qdrant payloads have 'content' which corresponds to document
            docs = [p.get("content", "") for p in payloads]
            metas = [{k: v for k, v in p.items() if k != "content"} for p in payloads]

            return VectorDBOutput(status="Success", results=docs, metadatas=metas)

        return VectorDBOutput(status=f"Error: Unknown action '{input_data.action}'")

    except Exception as e:
        return VectorDBOutput(status=f"VectorDB Operation Failed: {str(e)}")
