import asyncio
import functools
from typing import Callable, Any

def concurrent(func: Callable) -> Callable[..., Any]:
    """
    A decorator to run a synchronous, blocking function in a separate thread,
    making it non-blocking for an asyncio event loop.

    This decorator transforms a standard sync function into an async function
    that returns an awaitable coroutine.

    Usage:
        @concurrent
        def my_blocking_function(arg1, arg2):
            time.sleep(5)
            return "Done"

        async def main():
            result = await my_blocking_function("a", "b")

    Args:
        func: The synchronous function to wrap.

    Returns:
        An asynchronous wrapper function.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        """
        Asynchronous wrapper that executes the original function in a thread pool.
        """
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper
