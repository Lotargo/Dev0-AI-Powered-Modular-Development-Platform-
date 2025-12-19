import functools

def atomic(_func=None, *, version: str = "1.0"):
    """
    Декоратор для маркировки функции как "атомарного" модуля Dev0.

    Этот декоратор не изменяет логику функции, но добавляет к ней метаданные,
    которые используются индексатором для регистрации модуля в базе знаний.
    Может использоваться как `@atomic` или `@atomic(version="1.1")`.

    Args:
        version: Версия модуля.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # Прикрепляем метаданные непосредственно к объекту функции
        wrapper._is_atomic = True
        wrapper._atomic_version = version

        return wrapper

    if _func is None:
        # Вызван как @atomic(version="...")
        return decorator
    else:
        # Вызван как @atomic
        return decorator(_func)
