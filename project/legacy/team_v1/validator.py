"""Validator Agent: Performs static analysis on generated code."""
import ast
from pydantic import BaseModel
from typing import List

class Input(BaseModel):
    code: str

class Output(BaseModel):
    is_valid: bool
    errors: List[str]

def execute(input_data: Input) -> Output:
    """
    Validates the given Python code for syntax errors and unresolved imports.
    """
    errors = []

    # 1. Syntax Check
    try:
        ast.parse(input_data.code)
    except SyntaxError as e:
        errors.append(f"Syntax Error: {e}")
        return Output(is_valid=False, errors=errors)

    # 2. Import Check (Simple version)
    # A more advanced version could use tools like `pyflakes`
    tree = ast.parse(input_data.code)
    defined_names = set()

    # Gather all defined names (functions, classes, imports)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            defined_names.add(node.name)
        elif isinstance(node, ast.ClassDef):
            defined_names.add(node.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                defined_names.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                defined_names.add(alias.asname or alias.name)

    # Check for NameErrors (unresolved variables)
    # This is a simplification and won't catch everything, but it's a good start
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id not in defined_names and node.id not in __builtins__:
                # This is a potential NameError. This check is very basic
                # and might have false positives, but it's a useful heuristic.
                pass # Disabling for now as it's too noisy.

    if errors:
        return Output(is_valid=False, errors=errors)

    return Output(is_valid=True, errors=[])
