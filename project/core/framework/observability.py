from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable, Union
import json
import asyncio
import os
from datetime import datetime
import redis.asyncio as redis
from contextlib import asynccontextmanager
import functools
import inspect
import time
import uuid
from contextvars import ContextVar

# --- Context Vars ---
trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
span_id_var: ContextVar[Optional[str]] = ContextVar("span_id", default=None)

# --- Event Models ---

class Event:
    def __init__(self, type: str, source: str, data: Dict[str, Any], trace_id: Optional[str] = None, span_id: Optional[str] = None, parent_span_id: Optional[str] = None):
        self.type = type
        self.source = source
        self.data = data
        self.trace_id = trace_id
        self.span_id = span_id
        self.parent_span_id = parent_span_id
        # Use UTC now with timezone awareness if possible, else naive isoformat
        self.timestamp = datetime.utcnow().isoformat()

    def to_json(self) -> str:
        return json.dumps({
            "type": self.type,
            "source": self.source,
            "data": self.data,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "timestamp": self.timestamp
        })

    @classmethod
    def from_json(cls, json_str: str):
        d = json.loads(json_str)
        instance = cls(
            type=d["type"],
            source=d["source"],
            data=d["data"],
            trace_id=d.get("trace_id"),
            span_id=d.get("span_id"),
            parent_span_id=d.get("parent_span_id")
        )
        instance.timestamp = d.get("timestamp")
        return instance

# --- Abstract Bus ---

class EventBus(ABC):
    @abstractmethod
    async def publish(self, event: Event):
        pass

    @abstractmethod
    async def subscribe(self, channel: str):
        """Returns an async generator yielding events."""
        pass

# --- Redis Implementation ---

class RedisEventBus(EventBus):
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        self.pubsub = self.redis.pubsub()

    async def publish(self, event: Event):
        try:
            await self.redis.publish("dev0:events", event.to_json())
        except Exception as e:
            # Fail silently (or log) to prevent observability from breaking the app
            # specially when Redis is not available (e.g. local dev without docker)
            print(f"Observability Warning: Failed to publish event to Redis: {e}")

    async def subscribe(self, channel: str = "dev0:events"):
        async with self.redis.pubsub() as pubsub:
            await pubsub.subscribe(channel)
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        yield Event.from_json(message["data"])
                    except Exception as e:
                        print(f"Error parsing event: {e}")

# --- Factory ---

_bus_instance: Optional[EventBus] = None

def get_event_bus() -> EventBus:
    global _bus_instance
    if _bus_instance is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        _bus_instance = RedisEventBus(redis_url)
    return _bus_instance

# --- Decorators ---

def observable(source_name_or_func: Union[str, Callable] = None, *, source_name: str = None):
    """
    Decorator to monitor function execution.
    Emits EVENT_START, EVENT_COMPLETE, EVENT_ERROR.
    Manages Trace ID and Span ID.

    Usage:
        @observable
        async def func(): ...

        @observable(source_name="MyFunc")
        async def func(): ...
    """
    # Determine the actual source name override, if any
    # If positional argument was a string, use it.
    # If keyword argument was used, use it.
    name_override = source_name
    if isinstance(source_name_or_func, str):
        name_override = source_name_or_func

    def _decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            bus = get_event_bus()
            source = name_override or func.__name__

            # 1. Trace ID Management
            current_trace = trace_id_var.get()
            reset_trace_token = None
            if not current_trace:
                current_trace = str(uuid.uuid4())
                reset_trace_token = trace_id_var.set(current_trace)

            # 2. Span ID Management
            parent_span = span_id_var.get()
            current_span = str(uuid.uuid4())
            reset_span_token = span_id_var.set(current_span)

            # Prepare Data
            input_data = {
                "args": [str(a) for a in args],
                "kwargs": {k: str(v) for k, v in kwargs.items()}
            }

            await bus.publish(Event(
                type="EXECUTION_START",
                source=source,
                data=input_data,
                trace_id=current_trace,
                span_id=current_span,
                parent_span_id=parent_span
            ))

            start_time = time.time()
            try:
                result = await func(*args, **kwargs)

                duration = time.time() - start_time
                output_preview = str(result)[:500] if result else "None"

                await bus.publish(Event(
                    type="EXECUTION_COMPLETE",
                    source=source,
                    data={"duration": duration, "output_preview": output_preview},
                    trace_id=current_trace,
                    span_id=current_span,
                    parent_span_id=parent_span
                ))
                return result
            except Exception as e:
                duration = time.time() - start_time
                await bus.publish(Event(
                    type="EXECUTION_ERROR",
                    source=source,
                    data={"duration": duration, "error": str(e)},
                    trace_id=current_trace,
                    span_id=current_span,
                    parent_span_id=parent_span
                ))
                raise
            finally:
                # Restore Context
                if reset_span_token:
                    span_id_var.reset(reset_span_token)
                if reset_trace_token:
                    trace_id_var.reset(reset_trace_token)
        return wrapper

    if callable(source_name_or_func):
        # Called as @observable without arguments: source_name_or_func is the function
        return _decorator(source_name_or_func)
    else:
        # Called as factory: @observable("name") or @observable(source_name="name")
        return _decorator

# Helper for thoughts
async def emit_thought(source: str, content: str):
    """Explicitly emit a thought/reasoning event."""
    bus = get_event_bus()
    trace = trace_id_var.get()
    span = span_id_var.get()
    # Thoughts share the current span context
    await bus.publish(Event(
        type="AGENT_THOUGHT",
        source=source,
        data={"content": content},
        trace_id=trace,
        span_id=span,
        parent_span_id=None # Thoughts are leaves attached to a span
    ))
