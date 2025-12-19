import functools

def recipe(_func=None, *, version: str = "1.0"):
    """
    Декоратор для маркировки функции как "рецепта" Dev0.

    Рецепт — это композитный воркфлоу, собранный из атомарных модулей
    или других рецептов. Этот декоратор добавляет метаданные, которые
    используются индексатором для регистрации компонента в базе знаний.
    Может использоваться как `@recipe` или `@recipe(version="1.1")`.

    Args:
        version: Версия рецепта.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # Прикрепляем метаданные непосредственно к объекту функции
        wrapper._is_recipe = True
        wrapper._atomic_version = version # Using the same attribute for version for consistency

        return wrapper

    if _func is None:
        # Вызван как @recipe(version="...")
        return decorator
    else:
        # Вызван как @recipe
        return decorator(_func)
