"""
This module implements the @strict_types decorator, which uses the 'typeguard'
library to enforce runtime type checking for a function's arguments and
return values.
"""
import functools
from typeguard import typechecked

def strict_types(_func=None):
    """
    A decorator that enforces strict runtime type checking on a function.

    This decorator is essentially an alias for `typeguard.typechecked` but
    also attaches metadata to the function object, allowing the Dev0
    knowledge base indexer to recognize that this function operates under
    strict type constraints.

    Can be used as `@strict_types`.
    """
    def decorator(func):
        # Apply the typeguard checker first
        checked_func = typechecked(func)

        # Use functools.wraps to preserve the original function's metadata
        @functools.wraps(checked_func)
        def wrapper(*args, **kwargs):
            return checked_func(*args, **kwargs)

        # Attach our custom metadata for the indexer
        wrapper._is_strict_types = True
        return wrapper

    if _func is None:
        # Called as @strict_types()
        return decorator
    else:
        # Called as @strict_types
        return decorator(_func)

# For convenience, we can also make the raw typechecked available
# if needed elsewhere, though our pattern uses @strict_types
_typechecked = typechecked
