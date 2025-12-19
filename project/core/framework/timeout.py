"""
This module implements the @timeout decorator, providing a mechanism to prevent
long-running functions from blocking the system indefinitely.
"""
import functools
import asyncio
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Callable, Any

def timeout(seconds: int):
    """
    A decorator that raises a TimeoutError if the decorated function takes
    longer than a specified duration to execute.

    It supports both synchronous and asynchronous functions.

    Args:
        seconds: The maximum allowed execution time in seconds.
    """
    if seconds <= 0:
        raise ValueError("Timeout must be a positive integer.")

    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                try:
                    return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
                except asyncio.TimeoutError:
                    raise TimeoutError(f"Function {func.__name__} timed out after {seconds} seconds.")

            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                # Using a thread pool to run the function in a separate thread
                # allows us to join it with a timeout.
                executor = ThreadPoolExecutor(max_workers=1)
                future = executor.submit(func, *args, **kwargs)
                try:
                    return future.result(timeout=seconds)
                except FuturesTimeoutError:
                    raise TimeoutError(f"Function {func.__name__} timed out after {seconds} seconds.")
                finally:
                    executor.shutdown(wait=False)

            return sync_wrapper

    return decorator
