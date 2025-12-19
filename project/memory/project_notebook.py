"""
This module defines the ProjectNotebook class, which serves as a centralized,
serializable state manager for the AI orchestrator. It uses Redis for persistence.
"""
import json
from typing import Dict, Any, Optional
import redis.asyncio as redis
from pydantic import BaseModel, Field

# --- Redis Connection ---
import fakeredis.aioredis

# Singleton pattern to ensure a single Redis client instance.
_redis_client: Optional[redis.Redis] = None

import redis # Import top-level redis for exceptions

async def get_redis_client() -> redis.Redis:
    """
    Returns the singleton Redis client instance.
    Tries to connect to a real Redis server first, falls back to fakeredis if connection fails.
    This is an async function.
    """
    global _redis_client
    if _redis_client is None:
        try:
            real_redis_client = redis.asyncio.Redis(host='localhost', port=6379, db=0, decode_responses=True, socket_connect_timeout=1)
            await real_redis_client.ping()
            print("Successfully connected to a real Redis server.")
            _redis_client = real_redis_client
        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
            print("Real Redis server not found. Falling back to in-memory fakeredis.")
            _redis_client = fakeredis.aioredis.FakeRedis(decode_responses=True)

    return _redis_client

# --- Pydantic Models ---
class ModuleDetails(BaseModel):
    """Represents the details of a module to be implemented."""
    name: str
    description: str
    dependencies: list[str] = Field(default_factory=list)

class ImplementationDetails(BaseModel):
    """Represents the implementation details of a module."""
    code: str
    test_code: str
    filepath: str
    test_filepath: str

# --- Main Notebook Class ---
class ProjectNotebook(BaseModel):
    """
    A Pydantic-based notebook to maintain the state of the project generation.
    This class is responsible for loading from and saving to a Redis instance.
    """
    session_id: str
    task_prompt: str
    decomposed_plan: Dict[str, ModuleDetails] = Field(default_factory=dict)
    implementation_map: Dict[str, ImplementationDetails] = Field(default_factory=dict)
    validation_results: Dict[str, Any] = Field(default_factory=dict)
    review_feedback: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
        json_encoders = {
            redis.Redis: lambda v: "RedisClient"
        }

    @classmethod
    async def load(cls, session_id: str, task_prompt: str = "") -> 'ProjectNotebook':
        """
        Loads the notebook state from Redis for a given session_id.
        If no state is found, it initializes a new notebook.
        """
        r = await get_redis_client()
        redis_key = f"notebook:{session_id}"
        stored_data = await r.get(redis_key)

        if stored_data:
            data = json.loads(stored_data)
            # Ensure the loaded data has the current session_id
            data['session_id'] = session_id
            return cls(**data)

        # If no data found, create a new instance and save it
        new_notebook = cls(session_id=session_id, task_prompt=task_prompt)
        await new_notebook.save()
        return new_notebook

    async def save(self):
        """Saves the current state of the notebook to Redis."""
        r = await get_redis_client()
        redis_key = f"notebook:{self.session_id}"
        await r.set(redis_key, self.model_dump_json())

    def add_module(self, module_name: str, description: str, dependencies: list[str]):
        """Adds a new module to the decomposed plan."""
        self.decomposed_plan[module_name] = ModuleDetails(
            name=module_name,
            description=description,
            dependencies=dependencies
        )

    def add_implementation(self, module_name: str, code: str, test_code: str, filepath: str, test_filepath: str):
        """Adds the implementation details for a module."""
        self.implementation_map[module_name] = ImplementationDetails(
            code=code,
            test_code=test_code,
            filepath=filepath,
            test_filepath=test_filepath
        )

    def get_module_description(self, module_name: str) -> Optional[str]:
        """Retrieves the description for a specific module."""
        module = self.decomposed_plan.get(module_name)
        return module.description if module else None
