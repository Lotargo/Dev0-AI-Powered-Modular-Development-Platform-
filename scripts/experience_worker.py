"""
Experience Worker (Background Process):
This worker consumes experience events from a RabbitMQ queue, processes them
to generate "lessons," creates embeddings, and stores them in a persistent
VectorDB (ChromaDB).
"""
import asyncio
import json
from typing import Optional, Dict, Any
import aio_pika
import chromadb
from sentence_transformers import SentenceTransformer

# --- Global Clients (Initialized once per worker process) ---
_transformer_model: Optional[SentenceTransformer] = None
_chroma_client: Optional[chromadb.Client] = None

def get_transformer_model() -> SentenceTransformer:
    """Initializes and returns the singleton SentenceTransformer model."""
    global _transformer_model
    if _transformer_model is None:
        # Using a small, efficient model suitable for generating embeddings
        _transformer_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _transformer_model

def get_chroma_client() -> chromadb.Client:
    """Initializes and returns the singleton ChromaDB client."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path="./project/memory/databases/chroma_db")
    return _chroma_client

def generate_lesson(event: Dict[str, Any]) -> Optional[str]:
    """
    Generates a concise, actionable lesson from a raw experience event.
    """
    agent = event.get("agent_name")
    event_type = event.get("event_type")
    task = event.get("task_prompt")
    details = event.get("details", {})

    if event_type == "test_failure":
        error = details.get("error", "unknown error")
        return f"When tasked with '{task}', the code I wrote for the '{agent}' agent failed the tests with this error: '{error}'. I must avoid this mistake."
    elif event_type == "review_rejection":
        feedback = details.get("feedback", "no feedback provided")
        return f"During a review for the '{agent}' agent on the task '{task}', my solution was rejected. The feedback was: '{feedback}'. I need to incorporate this feedback in the future."
    elif event_type == "success":
        # Positive reinforcement is less critical for immediate correction,
        # but can be useful. For now, we focus on failures.
        return None
    return None

async def main():
    """Main worker loop to connect to RabbitMQ and process messages."""
    print("--- Experience Worker Started ---")
    print("Connecting to RabbitMQ...")
    try:
        connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
    except Exception as e:
        print(f"Failed to connect to RabbitMQ: {e}")
        print("Please ensure RabbitMQ server is running.")
        return

    async with connection:
        channel = await connection.channel()
        # Set prefetch_count to 1 to ensure a worker only handles one message at a time
        await channel.set_qos(prefetch_count=1)

        queue_name = "experience_queue"
        queue = await channel.declare_queue(queue_name, durable=True)
        print("Connection successful. Waiting for experience events...")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        event = json.loads(message.body.decode())
                        print(f"\nReceived event for agent: {event.get('agent_name')}")

                        lesson = generate_lesson(event)
                        if lesson:
                            print(f"  Generated lesson: {lesson[:100]}...")
                            model = get_transformer_model()
                            client = get_chroma_client()

                            collection_name = f"agent_experiences_{event.get('agent_name')}"
                            collection = client.get_or_create_collection(name=collection_name)

                            # Use a hash of the lesson as a unique ID to prevent duplicates
                            lesson_id = str(hash(lesson))

                            # Add the lesson, embedding, and metadata to ChromaDB
                            collection.add(
                                embeddings=[model.encode(lesson).tolist()],
                                documents=[lesson],
                                metadatas=[{"source_event": event.get("event_type")}],
                                ids=[lesson_id]
                            )
                            print(f"  Successfully processed and stored lesson '{lesson_id}' in collection '{collection_name}'.")
                        else:
                            print("  Event did not result in a new lesson. Discarding.")

                        if queue.name in message.body.decode():
                            break
                    except Exception as e:
                        print(f"  Error processing message: {e}")
                        # Optionally, you could requeue the message or move it to a dead-letter queue
    print("--- Experience Worker Shutdown ---")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Worker stopped by user.")
