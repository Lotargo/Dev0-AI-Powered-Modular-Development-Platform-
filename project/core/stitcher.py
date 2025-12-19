import ast
import astor

# Эта карта сопоставляет имя свойства (из рецепта Архитектора)
# с путем импорта и именем самого декоратора.
DECORATOR_MAP = {
    "atomic": ("project.core.framework.atomic", "atomic"),
    # В будущем здесь можно будет добавить новые декораторы
    # "sandbox": ("project.core.framework.sandbox", "sandbox"),
}

def stitch_decorators(source_code: str, properties: list[str]) -> str:
    """
    Программно добавляет декораторы к исходному коду функции.

    Использует AST для безопасной модификации кода, добавляя необходимые
    импорты и применяя декораторы к первой найденной функции в коде.

    Args:
        source_code: Исходный код Python в виде строки.
        properties: Список свойств (имен декораторов) для применения.

    Returns:
        Модифицированный исходный код с добавленными декораторами.

    Raises:
        ValueError: Если в коде не найдена ни одна функция.
    """
    tree = ast.parse(source_code)

    function_def = None
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            function_def = node
            break

    if function_def is None:
        raise ValueError("Не удалось найти определение функции в исходном коде.")

    # Добавляем импорты и декораторы в обратном порядке, чтобы они
    # оказались в правильном порядке в итоговом файле (импорты сверху,
    # декораторы в порядке применения).
    for prop in reversed(properties):
        if prop in DECORATOR_MAP:
            module_path, decorator_name = DECORATOR_MAP[prop]

            # 1. Создаем узел импорта
            import_node = ast.ImportFrom(
                module=module_path,
                names=[ast.alias(name=decorator_name, asname=None)],
                level=0
            )
            # Вставляем импорт в начало файла
            tree.body.insert(0, import_node)

            # 2. Создаем узел декоратора
            # Для простоты пока считаем, что все декораторы вызываются без аргументов,
            # например @atomic, а не @atomic(). Для вызова нужен ast.Call.
            decorator_node = ast.Name(id=decorator_name, ctx=ast.Load())

            # Вставляем декоратор в начало списка декораторов функции
            function_def.decorator_list.insert(0, decorator_node)

    # Преобразуем измененное AST обратно в код
    # astor добавляет лишние пустые строки, их можно будет убрать при необходимости
    new_source_code = astor.to_source(tree)
    return new_source_code
