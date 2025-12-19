import importlib.util
import sys
from types import ModuleType

def load_module_from_code(code: str, module_name: str = "temp_module") -> ModuleType:
    """
    Динамически загружает Python-модуль из строки с кодом.

    Это позволяет тестировать сгенерированный код, который еще не сохранен
    в файл и не является частью установленного пакета.

    Args:
        code: Строка с исходным кодом Python.
        module_name: Имя для создаваемого модуля.

    Returns:
        Загруженный модуль как объект.
    """
    # Удаляем модуль, если он уже был загружен (важно для повторных запусков)
    if module_name in sys.modules:
        del sys.modules[module_name]

    spec = importlib.util.spec_from_loader(module_name, loader=None)
    module = importlib.util.module_from_spec(spec)

    exec(code, module.__dict__)

    sys.modules[module_name] = module
    return module
