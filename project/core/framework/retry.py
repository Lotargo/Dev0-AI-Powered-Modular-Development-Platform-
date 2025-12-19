"""
This module implements the @retry decorator, providing resilience for functions
that may fail intermittently (e.g., network requests).
"""
import functools
import time
import asyncio
from typing import Callable, Any

def retry(attempts: int = 3, delay: float = 1.0):
    """
    A decorator that retries a function call if it raises an exception.

    It supports both synchronous and asynchronous functions.

    Args:
        attempts: The maximum number of times to try the function.
        delay: The delay in seconds between retries.
    """
    if attempts < 1:
        raise ValueError("Number of attempts must be at least 1.")
    if delay < 0:
        raise ValueError("Delay must be a non-negative number.")

    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                last_exception = None
                for attempt in range(attempts):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        print(f"Attempt {attempt + 1}/{attempts} failed: {e}. Retrying in {delay}s...")
                        await asyncio.sleep(delay)
                raise last_exception

            # Attach metadata for the indexer
            async_wrapper._is_retryable = True
            async_wrapper._retry_attempts = attempts
            async_wrapper._retry_delay = delay
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                last_exception = None
                for attempt in range(attempts):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        print(f"Attempt {attempt + 1}/{attempts} failed: {e}. Retrying in {delay}s...")
                        time.sleep(delay)
                raise last_exception

            # Attach metadata for the indexer
            sync_wrapper._is_retryable = True
            sync_wrapper._retry_attempts = attempts
            sync_wrapper._retry_delay = delay
            return sync_wrapper

    return decorator
