import chromadb
import sqlalchemy
from sqlalchemy import create_engine, Column, String, Boolean, Text, JSON
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import json
from typing import List, Type
import uuid

from project.memory.models import BaseExperience
from project.memory.embedding_manager import EmbeddingManager

Base = declarative_base()

class ExperienceDB(Base):
    __tablename__ = 'experiences'
    session_id = Column(String, primary_key=True)
    success = Column(Boolean)
    # Generic fields, specific data stored in a JSON blob
    details = Column(JSON)

class StorageManager:
    """
    Управляет хранением и извлечением "опыта" для конкретного агента.
    Каждый экземпляр работает с собственной, изолированной базой данных.
    """
    def __init__(self, db_name: str, embedding_manager: EmbeddingManager, experience_model: Type[BaseExperience]):
        """
        Инициализирует StorageManager для конкретной базы данных.

        Args:
            db_name: Уникальное имя для базы данных (e.g., 'planner', 'engineer').
            embedding_manager: Экземпляр EmbeddingManager.
            experience_model: Pydantic-модель, определяющая структуру опыта.
        """
        # ChromaDB setup for vector storage
        self.client = chromadb.PersistentClient(path=f"chroma_{db_name}")
        self.collection = self.client.get_or_create_collection(f"{db_name}_experiences")

        # SQLite setup for metadata storage
        self.database_url = f"sqlite:///{db_name}_experience.db"
        self.engine = create_engine(self.database_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        self.embedding_manager = embedding_manager
        self.experience_model = experience_model

    def record_experience(self, experience: BaseExperience, text_for_embedding: str):
        """
        Сохраняет новый опыт в ChromaDB и SQLite.

        Args:
            experience: Экземпляр Pydantic-модели опыта.
            text_for_embedding: Текст, который будет векторизован для поиска.
        """
        db = self.SessionLocal()
        db_experience = ExperienceDB(
            session_id=experience.session_id,
            success=experience.success,
            details=experience.model_dump()
        )
        db.add(db_experience)
        db.commit()
        db.close()

        embedding = self.embedding_manager.get_embedding(text_for_embedding).tolist()
        self.collection.add(
            embeddings=[embedding],
            metadatas=[{"session_id": experience.session_id}],
            ids=[experience.session_id]
        )

    def retrieve_relevant_experiences(self, query_text: str, n_results: int = 3) -> List[BaseExperience]:
        """
        Извлекает наиболее релевантный прошлый опыт на основе запроса.
        """
        query_embedding = self.embedding_manager.get_embedding(query_text).tolist()
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        if not results['ids'][0]:
            return []

        db = self.SessionLocal()
        session_ids = results['ids'][0]
        experiences_db = db.query(ExperienceDB).filter(ExperienceDB.session_id.in_(session_ids)).all()
        db.close()

        # Re-create Pydantic models from the stored JSON
        return [self.experience_model(**exp.details) for exp in experiences_db]
