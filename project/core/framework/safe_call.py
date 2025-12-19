"""
This module implements the @safe_call decorator, which wraps a function's
execution in a try-except block, emulating the Result<T, E> pattern from Rust.
"""
import functools
import asyncio
from pydantic import BaseModel
from typing import Any, Optional, Type

# We use a generic Pydantic model here, but the actual return type of the
# decorated function will be this SafeCallResult model.
class SafeCallResult(BaseModel):
    """
    A Pydantic model to represent the result of a fallible operation.
    It will contain either a 'value' on success or an 'error' on failure.
    """
    value: Optional[Any] = None
    error: Optional[str] = None

def safe_call(_func=None):
    """
    A decorator that makes a function's error handling explicit.

    Instead of raising an exception, a function decorated with @safe_call will
    return a `SafeCallResult` object. This forces the caller to consciously
    handle the possibility of an error, similar to Rust's Result or Go's
    `if err != nil` pattern.

    Can be used as `@safe_call`.
    """
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> SafeCallResult:
                try:
                    result_value = await func(*args, **kwargs)
                    return SafeCallResult(value=result_value, error=None)
                except Exception as e:
                    return SafeCallResult(value=None, error=str(e))
            async_wrapper._is_safe_call = True
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> SafeCallResult:
                try:
                    result_value = func(*args, **kwargs)
                    return SafeCallResult(value=result_value, error=None)
                except Exception as e:
                    # We capture the exception and return it as part of the result
                    return SafeCallResult(value=None, error=str(e))

            # Attach metadata for the indexer
            sync_wrapper._is_safe_call = True
            return sync_wrapper

    if _func is None:
        # Called as @safe_call() - not currently supported with args but allows parentheses
        return decorator
    else:
        # Called as @safe_call
        return decorator(_func)
