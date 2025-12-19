"""
This module implements the @immutable_args decorator, which prevents side effects
by passing deep copies of mutable arguments (Pydantic models, dicts, lists)
to the decorated function.
"""
import functools
import copy
from pydantic import BaseModel

def immutable_args(_func=None):
    """
    A decorator that protects the caller's data from side effects.

    It performs a deep copy on any Pydantic models, `dict`, or `list`
    arguments before passing them to the actual function. This is crucial for
    our architecture as modules receive Pydantic models as inputs. This ensures
    that modifications made inside the function do not affect the original
    objects, emulating immutability from languages like Rust.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            copied_args = []
            for arg in args:
                if isinstance(arg, BaseModel):
                    copied_args.append(arg.copy(deep=True))
                elif isinstance(arg, (dict, list)):
                    copied_args.append(copy.deepcopy(arg))
                else:
                    copied_args.append(arg)

            copied_kwargs = {}
            for key, value in kwargs.items():
                if isinstance(value, BaseModel):
                    copied_kwargs[key] = value.copy(deep=True)
                elif isinstance(value, (dict, list)):
                    copied_kwargs[key] = copy.deepcopy(value)
                else:
                    copied_kwargs[key] = value

            return func(*copied_args, **copied_kwargs)

        # Attach our custom metadata for the indexer
        wrapper._has_immutable_args = True
        return wrapper

    if _func is None:
        # Called as @immutable_args()
        return decorator
    else:
        # Called as @immutable_args
        return decorator(_func)
