import pytest
from project.core.stitcher import stitch_decorators

def test_stitch_single_decorator():
    """
    Проверяет, что сборщик правильно добавляет один декоратор и импорт.
    """
    source_code = """
def my_function(x):
    return x + 1
"""
    properties = ["atomic"]

    stitched_code = stitch_decorators(source_code, properties)

    # Убираем лишние пустые строки для удобства сравнения
    stitched_code_clean = "\n".join(line for line in stitched_code.split('\n') if line.strip())

    expected_code = """
from project.core.framework.atomic import atomic
@atomic
def my_function(x):
    return x + 1
"""
    expected_code_clean = "\n".join(line for line in expected_code.split('\n') if line.strip())

    assert stitched_code_clean == expected_code_clean

def test_stitch_no_properties():
    """
    Проверяет, что если нет свойств, код остается неизменным.
    """
    source_code = """
def my_function(x):
    return x + 1
"""
    properties = []

    stitched_code = stitch_decorators(source_code, properties)

    # astor может добавлять/убирать пустые строки, поэтому сравниваем по наличию
    assert "def my_function(x):" in stitched_code
    assert "return x + 1" in stitched_code

def test_stitch_no_function_error():
    """
    Проверяет, что сборщик вызывает ошибку, если в коде нет функции.
    """
    source_code = "x = 10"
    properties = ["atomic"]

    with pytest.raises(ValueError, match="Не удалось найти определение функции"):
        stitch_decorators(source_code, properties)
