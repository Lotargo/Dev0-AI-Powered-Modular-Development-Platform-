"""
Experience Recorder (Command Side of CQRS):
This module is responsible for capturing an experience and sending it to a
message queue (RabbitMQ) for asynchronous processing.
"""
import json
import asyncio
from pydantic import BaseModel
from typing import Dict, Any, Optional
import aio_pika

# --- RabbitMQ Connection ---
_rabbitmq_connection: Optional[aio_pika.Connection] = None

async def get_rabbitmq_connection() -> aio_pika.Connection:
    """Returns the singleton RabbitMQ connection instance."""
    global _rabbitmq_connection
    if _rabbitmq_connection is None or _rabbitmq_connection.is_closed:
        # In a real application, connection details would come from a config file.
        _rabbitmq_connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
    return _rabbitmq_connection

# --- Pydantic Models ---
class Input(BaseModel):
    session_id: str
    task_prompt: str
    agent_name: str
    event_type: str  # e.g., "test_failure", "review_rejection", "success"
    details: Dict[str, Any]

class Output(BaseModel):
    status: str
    message: str

# --- Core Logic ---
async def execute_async(input_data: Input) -> Output:
    """
    Publishes an agent's experience to the RabbitMQ queue.
    """
    try:
        connection = await get_rabbitmq_connection()
        async with connection.channel() as channel:
            # Declare the queue, durable=True means it survives broker restarts
            queue_name = "experience_queue"
            await channel.declare_queue(queue_name, durable=True)

            # Prepare the message
            message_body = input_data.model_dump_json().encode()
            message = aio_pika.Message(
                body=message_body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT  # Make message persistent
            )

            # Publish the message
            await channel.default_exchange.publish(message, routing_key=queue_name)

        return Output(status="success", message="Experience event published successfully.")
    except Exception as e:
        # In a real system, you'd have more robust error handling and logging
        return Output(status="error", message=f"Failed to publish experience event: {e}")

def execute(input_data: Input) -> Output:
    """Synchronous wrapper for the async execute function."""
    return asyncio.run(execute_async(input_data))
