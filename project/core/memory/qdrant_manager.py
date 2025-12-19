"""
Qdrant Manager: Handles vector database operations for the project.
Acts as the "Brain" storage mechanism.
"""
import os
import logging
from typing import List, Dict, Any, Optional, Union
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer

# Configuration
QDRANT_PATH = os.getenv("QDRANT_STORAGE_PATH", os.path.join(os.getcwd(), "qdrant_storage"))
COLLECTION_KNOWLEDGE_BASE = "knowledge_base"
COLLECTION_EXPERIENCES = "experiences"
COLLECTION_CODEBASE = "codebase"
COLLECTION_DOCUMENTATION = "documentation"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2" # Lightweight and fast

logger = logging.getLogger(__name__)

class ScoredItem(dict):
    """A dictionary wrapper that includes a score attribute."""
    def __init__(self, payload: Dict[str, Any], score: float):
        super().__init__(payload)
        self.score = score

class QdrantManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(QdrantManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        qdrant_url = os.getenv("QDRANT_URL")

        if qdrant_url:
            print(f"--- Initializing QdrantManager (Server Mode: {qdrant_url}) ---")
            self.client = QdrantClient(url=qdrant_url)
        else:
            print(f"--- Initializing QdrantManager (Local Mode: {QDRANT_PATH}) ---")
            self.client = QdrantClient(path=QDRANT_PATH)

        # Lazy load model
        self._model = None

        self._initialized = True

    @property
    def model(self):
        if self._model is None:
            print(f"--- Loading Embedding Model: {EMBEDDING_MODEL_NAME} ---")
            self._model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        return self._model

    def _get_embedding(self, text: str) -> List[float]:
        """Generates a vector embedding for the given text."""
        return self.model.encode(text).tolist()

    def ensure_collection(self, collection_name: str, vector_size: int = 384):
        """Creates the collection if it doesn't exist."""
        collections = self.client.get_collections()
        exists = any(c.name == collection_name for c in collections.collections)

        if not exists:
            print(f"--- Creating Qdrant Collection: {collection_name} ---")
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE
                )
            )

    def upsert_module(self, module_data: Dict[str, Any]):
        """
        Indexes a module (or recipe) into the knowledge base.
        """
        self.ensure_collection(COLLECTION_KNOWLEDGE_BASE)

        # Create text for embedding: Name + Description + Inputs
        # We want semantically relevant search.
        name = module_data.get("name", "")
        description = module_data.get("description", "")
        docstring = f"{name}: {description}"

        vector = self._get_embedding(docstring)

        # Point ID: Hash of import_path to be deterministic
        import_path = module_data.get("import_path", "")
        point_id = self._generate_id(import_path)

        self.client.upsert(
            collection_name=COLLECTION_KNOWLEDGE_BASE,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=module_data
                )
            ]
        )

    def search_tools(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Searches for relevant tools in the knowledge base.
        """
        # Return raw payloads for tools
        items = self.search_items(COLLECTION_KNOWLEDGE_BASE, query, limit)
        return [dict(item) for item in items]

    def search_items(self, collection_name: str, query: str, limit: int = 5) -> List[ScoredItem]:
        """
        Generic semantic search.
        Returns a list of ScoredItem (dict-like objects with a .score attribute).
        """
        self.ensure_collection(collection_name)
        vector = self._get_embedding(query)

        results = self.client.query_points(
            collection_name=collection_name,
            query=vector,
            limit=limit
        ).points

        # Wrap payload in ScoredItem to preserve the score
        return [ScoredItem(hit.payload, hit.score) for hit in results]

    def add_item(self, collection_name: str, text: str, metadata: Dict[str, Any], item_id: str = None):
        """Adds a single item to the vector DB."""
        self.ensure_collection(collection_name)
        vector = self._get_embedding(text)

        if not item_id:
            item_id = self._generate_id(text)

        # Ensure ID is valid UUID if possible, or generic string hash
        # Qdrant prefers UUIDs.
        try:
            import uuid
            uuid.UUID(item_id)
        except ValueError:
            item_id = self._generate_id(item_id)

        from qdrant_client.http import models
        self.client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=item_id,
                    vector=vector,
                    payload={**metadata, "content": text}
                )
            ]
        )

    def _generate_id(self, unique_string: str) -> str:
        """Generates a deterministic UUID based on a string."""
        import uuid
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, unique_string))

    def clear_collection(self, collection_name: str):
        """Deletes and recreates a collection."""
        try:
            self.client.delete_collection(collection_name)
        except Exception:
            pass
        self.ensure_collection(collection_name)

    def close(self):
        """Closes the Qdrant client connection."""
        if self.client:
            self.client.close()

# Singleton accessor
def get_qdrant_manager() -> QdrantManager:
    return QdrantManager()
