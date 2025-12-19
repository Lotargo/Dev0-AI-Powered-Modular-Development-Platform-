import asyncio
import uuid
import time
import os
from project.core.framework.observability import RedisEventBus, Event

async def inject_trace():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    bus = RedisEventBus(redis_url)

    print(f"Injecting fake trace to {redis_url}...")

    # 1. Root Span (Orchestrator)
    root_trace_id = str(uuid.uuid4())
    root_span_id = str(uuid.uuid4())

    await bus.publish(Event(
        type="EXECUTION_START",
        source="Orchestrator",
        data={"args": ["Create a snake game"]},
        trace_id=root_trace_id,
        span_id=root_span_id,
        parent_span_id=None
    ))

    time.sleep(0.1)

    # 2. Child Span (Architect)
    child_span_id = str(uuid.uuid4())
    await bus.publish(Event(
        type="EXECUTION_START",
        source="ArchitectAgent",
        data={"args": ["Create a snake game", "feedback=None"]},
        trace_id=root_trace_id,
        span_id=child_span_id,
        parent_span_id=root_span_id
    ))

    time.sleep(0.2)

    # 3. Thought (Architect)
    await bus.publish(Event(
        type="AGENT_THOUGHT",
        source="ArchitectAgent",
        data={"content": "I need to use the 'create_file' tool to build the main game loop."},
        trace_id=root_trace_id,
        span_id=child_span_id,
        parent_span_id=None
    ))

    time.sleep(0.5)

    # 4. Complete Child
    await bus.publish(Event(
        type="EXECUTION_COMPLETE",
        source="ArchitectAgent",
        data={"duration": 0.7, "output_preview": "Created recipe_snake.py"},
        trace_id=root_trace_id,
        span_id=child_span_id,
        parent_span_id=root_span_id
    ))

    time.sleep(0.1)

    # 5. Complete Root
    await bus.publish(Event(
        type="EXECUTION_COMPLETE",
        source="Orchestrator",
        data={"duration": 1.5, "output_preview": "Success"},
        trace_id=root_trace_id,
        span_id=root_span_id,
        parent_span_id=None
    ))

    print("Injection complete.")
    # We need to close the redis client connection properly
    await bus.redis.aclose()

if __name__ == "__main__":
    asyncio.run(inject_trace())
