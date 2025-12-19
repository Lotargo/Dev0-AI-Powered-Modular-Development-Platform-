"""
This module is responsible for discovering, parsing, and indexing all the
building blocks (modules, adapters, recipes) available in the project.
"""
import os
import ast
import json
from typing import List, Dict, Optional, Any

MODULE_DIRS = ["project/modules", "project/adapters", "project/recipes"]
BASE_DIR = os.getcwd()

class BuildingBlock(Dict):
    name: str
    type: str
    filepath: str
    import_path: str
    description: str
    schemas: Dict[str, Any]
    metadata: Dict[str, Any]

def _get_pydantic_schemas(tree: ast.AST) -> Dict[str, Any]:
    """
    Extracts Pydantic schemas by finding the 'execute' function and resolving
    its input and output type hints to the class definitions in the file.
    """
    schemas: Dict[str, Any] = {
        "Input": {"class_name": None, "fields": {}},
        "Output": {"class_name": None, "fields": {}}
    }
    execute_func = None
    classes = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes[node.name] = node
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in ("execute", "execute_async"):
            execute_func = node

    if not execute_func:
        return schemas

    if execute_func.args.args:
        input_arg = next((arg for arg in execute_func.args.args if arg.arg != 'self'), None)
        if input_arg and input_arg.annotation and isinstance(input_arg.annotation, ast.Name):
            input_class_name = input_arg.annotation.id
            schemas["Input"]["class_name"] = input_class_name
            if input_class_name in classes:
                for stmt in classes[input_class_name].body:
                    if isinstance(stmt, ast.AnnAssign):
                        field_name = stmt.target.id
                        field_type = ast.unparse(stmt.annotation)
                        schemas["Input"]["fields"][field_name] = field_type

    if execute_func.returns and isinstance(execute_func.returns, ast.Name):
        output_class_name = execute_func.returns.id
        # Special handling for safe_call, the *actual* output is in the generic
        if output_class_name == 'SafeCallResult' and isinstance(execute_func.returns, ast.Subscript):
             # Try to find the actual return type like SafeCallResult[RealOutput]
            actual_return_node = execute_func.returns.slice
            if isinstance(actual_return_node, ast.Name):
                 output_class_name = actual_return_node.id

        schemas["Output"]["class_name"] = output_class_name
        if output_class_name in classes:
            for stmt in classes[output_class_name].body:
                if isinstance(stmt, ast.AnnAssign):
                    field_name = stmt.target.id
                    field_type = ast.unparse(stmt.annotation)
                    schemas["Output"]["fields"][field_name] = field_type

    return schemas

def _parse_module_ast(filepath: str) -> (Optional[str], Dict[str, Any], Dict[str, Any]):
    """
    Extracts docstring, Pydantic schemas, and decorator metadata from a Python file.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)

        schemas = _get_pydantic_schemas(tree)
        docstring = None
        metadata = {}

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in ("execute", "execute_async"):
                docstring = ast.get_docstring(node)

                for decorator in node.decorator_list:
                    decorator_name = ""
                    decorator_args = {}
                    if isinstance(decorator, ast.Name):
                        decorator_name = decorator.id
                    elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
                        decorator_name = decorator.func.id
                        for keyword in decorator.keywords:
                            decorator_args[keyword.arg] = ast.literal_eval(keyword.value)

                    if decorator_name in ['atomic', 'recipe']:
                        metadata['type'] = decorator_name
                        if decorator_args:
                            metadata.update(decorator_args)

                    if decorator_name == 'safe_call':
                        metadata['is_safe_call'] = True
                        schemas['Output']['class_name'] = 'SafeCallResult'

                    if decorator_name == 'strict_types':
                        metadata['is_strict_types'] = True

                    if decorator_name == 'immutable_args':
                        metadata['has_immutable_args'] = True

                    if decorator_name == 'retry':
                        metadata['is_retryable'] = True
                        metadata['retry_config'] = decorator_args if decorator_args else {'attempts': 3, 'delay': 1.0} # Default values if used as @retry

                    if decorator_name == 'timeout':
                        metadata['has_timeout'] = True
                        metadata['timeout_config'] = decorator_args

                    if decorator_name == 'concurrent':
                        metadata['is_concurrent'] = True

        if not docstring:
            docstring = ast.get_docstring(tree)

        return docstring, schemas, metadata
    except Exception:
        return None, {"Input": {"class_name": None, "fields": {}}, "Output": {"class_name": None, "fields": {}}}, {}


def discover_blocks() -> List[BuildingBlock]:
    """Scans the project directories to find all building blocks."""
    blocks = []
    for dir_path in MODULE_DIRS:
        full_dir_path = os.path.join(BASE_DIR, dir_path)

        for root, _, files in os.walk(full_dir_path):
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    filepath = os.path.join(root, file)
                    name = file.removesuffix(".py")
                    relative_path = os.path.relpath(filepath, BASE_DIR)
                    import_path = relative_path.replace(os.sep, ".").removesuffix(".py")
                    description, schemas, metadata = _parse_module_ast(filepath)

                    if not metadata.get('type'):
                        continue

                    block = BuildingBlock(
                        name=name,
                        type=metadata.get('type'),
                        filepath=filepath,
                        import_path=import_path,
                        description=(description or "No description available.").strip(),
                        schemas=schemas,
                        metadata=metadata
                    )
                    blocks.append(block)
    return blocks

def create_knowledge_base(output_path: str = "modules_db.json"):
    """Discovers all building blocks and saves them to a JSON file."""
    blocks = discover_blocks()
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(blocks, f, indent=4, ensure_ascii=False)

def main():
    """Main function to create the knowledge base."""
    create_knowledge_base()

if __name__ == "__main__":
    main()
