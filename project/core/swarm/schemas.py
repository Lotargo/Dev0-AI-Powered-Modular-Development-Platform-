"""
Swarm Data Structures (Neuro-Packet)

This module defines the standardized data format for exchanging 'Golden Lessons'
between Dev0 instances in the P2P network.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict
from datetime import datetime
import hashlib

class KnowledgePayload(BaseModel):
    """The core actionable knowledge."""
    problem_pattern: str = Field(..., description="Abstract description of the error/task.")
    solution_snippet: str = Field(..., description="Universal code solution (Golden Snippet).")
    dependencies: List[str] = Field(default_factory=list, description="Required PyPI packages.")
    key_insight: str = Field(..., description="One-sentence rule or insight.")

class NetworkMeta(BaseModel):
    """Metadata for validation and routing."""
    author_hash: str = Field(..., description="Anonymous ID of the author node.")
    validation_score: float = Field(0.0, description="Reliability score (0.0 - 1.0).")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    protocol_version: str = Field("1.0", description="Version of the Neuro-Packet format.")

class NetworkLesson(BaseModel):
    """
    The 'Neuro-Packet' - A standardized unit of knowledge for the Hive.
    """
    id: str = Field(..., description="Unique Hash ID of the lesson.")
    vector_hash: str = Field(..., description="Hash of the embedding vector (for quick lookup).")
    topic_embedding: List[float] = Field(..., description="Semantic vector (384 float) for search.")
    payload: KnowledgePayload
    meta: NetworkMeta

    @staticmethod
    def generate_id(content: str) -> str:
        """Generates a deterministic hash ID from content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
