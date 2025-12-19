"""
This module defines the project compiler. It packages a recipe and its
dependencies into a self-contained, standalone project directory using
static code analysis (AST).
"""
import ast
import shutil
import toml
from pathlib import Path
from typing import Set, Tuple
from pydantic import BaseModel, Field
from project.core.infrastructure.dependency_resolver import dependency_resolver

# --- Constants ---
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
EXPORTED_PROJECTS_DIR = PROJECT_ROOT / "exported_projects"

# --- Pydantic Models ---
class CompileProjectInput(BaseModel):
    recipe_filepath: str = Field(..., description="The absolute path to the recipe file to compile.")

class CompileProjectOutput(BaseModel):
    message: str = Field(..., description="The result of the compilation.")
    export_path: str = Field(..., description="The path to the exported project directory.")

def parse_requirements_from_docstring(source_code: str) -> Set[str]:
    deps = set()
    try:
        tree = ast.parse(source_code)
        docstring = ast.get_docstring(tree)
        if docstring:
            for line in docstring.split('\n'):
                if "Requirements:" in line:
                    reqs = line.split("Requirements:")[1].strip()
                    for r in reqs.split(','):
                        clean_r = r.strip()
                        if clean_r:
                            deps.add(clean_r)
    except Exception:
        pass
    return deps

# --- AST Dependency Analyzer ---
class DependencyVisitor(ast.NodeVisitor):
    def __init__(self, source_file: Path):
        self.source_file = source_file
        self.local_deps: Set[Path] = set()
        self.external_deps: Set[str] = set()
        self.project_root = PROJECT_ROOT

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            if alias.name.startswith("project."):
                self._resolve_and_add(alias.name.split('.'))
            else:
                self.external_deps.add(alias.name.split('.')[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module and node.module.startswith("project."):
            module_parts = node.module.split('.')
            for alias in node.names:
                # Handles 'from project.modules.filesystem import create_file'
                # by trying to resolve 'project/modules/filesystem/create_file.py'
                path_to_try = module_parts + [alias.name]
                if not self._resolve_and_add(path_to_try):
                    # If that fails, it must be that the module is the dependency
                    # e.g., 'from project.modules.filesystem.create_file import execute'
                    self._resolve_and_add(module_parts)
        elif node.module:
            self.external_deps.add(node.module.split('.')[0])
        self.generic_visit(node)

    def _resolve_and_add(self, path_parts: list[str]) -> bool:
        """
        Tries to resolve a path from parts and adds it to dependencies.
        Returns True if successful, False otherwise.
        """
        # Remove 'project' from the start
        relative_parts = path_parts[1:]

        # Try to resolve as a .py file
        potential_path = self.project_root / 'project' / Path(*relative_parts).with_suffix('.py')
        if potential_path.is_file():
            self.local_deps.add(potential_path)
            # Add all __init__.py files in the parent directories
            parent = potential_path.parent
            while self.project_root in parent.parents:
                init_py = parent / '__init__.py'
                if init_py.is_file():
                    self.local_deps.add(init_py)
                parent = parent.parent
            return True

        # Try to resolve as a directory with __init__.py
        potential_path = self.project_root / 'project' / Path(*relative_parts) / '__init__.py'
        if potential_path.is_file():
            self.local_deps.add(potential_path)
            return True

        return False

    def visit_Call(self, node: ast.Call):
        """
        Visit a function call to find 'hidden' dependencies inside string literals
        passed to specific functions like 'python_executor'.
        """
        # Check if the function being called is our aliased 'python_executor'
        if isinstance(node.func, ast.Name) and node.func.id == 'python_executor':
            if node.args and isinstance(node.args[0], ast.Call):
                input_model_call = node.args[0]

                code_arg_node = None
                # Find the 'command' argument, whether positional or keyword
                if input_model_call.args:
                    code_arg_node = input_model_call.args[0]
                else:
                    for keyword in input_model_call.keywords:
                        if keyword.arg == 'command':
                            code_arg_node = keyword.value
                            break

                code_string = None
                # Case 1: The code is a string literal
                if isinstance(code_arg_node, ast.Constant) and isinstance(code_arg_node.s, str):
                    code_string = code_arg_node.s
                # Case 2: The code is in a variable. Find where it was assigned.
                elif isinstance(code_arg_node, ast.Name):
                    var_name = code_arg_node.id

                    # This visitor will find the assignment to our target variable
                    class AssignmentFinder(ast.NodeVisitor):
                        def __init__(self, target_var):
                            self.target_var = target_var
                            self.found_code = None

                        def visit_Assign(self, assign_node):
                            # We only care about single assignments like 'x = "..."'
                            if len(assign_node.targets) == 1 and isinstance(assign_node.targets[0], ast.Name):
                                if assign_node.targets[0].id == self.target_var:
                                    if isinstance(assign_node.value, ast.Constant) and isinstance(assign_node.value.s, str):
                                        self.found_code = assign_node.value.s
                            self.generic_visit(assign_node)

                    try:
                        full_tree = ast.parse(open(self.source_file, "r", encoding="utf-8").read())
                        finder = AssignmentFinder(var_name)
                        finder.visit(full_tree)
                        code_string = finder.found_code
                    except (FileNotFoundError, SyntaxError):
                        pass

                if code_string:
                    try:
                        inner_tree = ast.parse(code_string)
                        inner_visitor = DependencyVisitor(self.source_file)
                        inner_visitor.visit(inner_tree)
                        self.external_deps.update(inner_visitor.external_deps)
                    except SyntaxError:
                        pass # Ignore syntax errors in the inner string

        self.generic_visit(node)

def analyze_dependencies(filepath: Path, visited: Set[Path] = None) -> Tuple[Set[Path], Set[str]]:
    if visited is None:
        visited = set()
    if filepath in visited:
        return set(), set()
    visited.add(filepath)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source_code = f.read()
        tree = ast.parse(source_code)
    except (FileNotFoundError, SyntaxError):
        return set(), set()

    visitor = DependencyVisitor(filepath)
    visitor.visit(tree)

    local_deps = visitor.local_deps
    external_deps = visitor.external_deps

    # Parse explicit requirements from docstring
    doc_reqs = parse_requirements_from_docstring(source_code)
    external_deps.update(doc_reqs)

    # Итерируемся по копии, чтобы избежать ошибки "Set changed size during iteration"
    for dep_path in visitor.local_deps.copy():
        recursive_local, recursive_external = analyze_dependencies(dep_path, visited)
        local_deps.update(recursive_local)
        external_deps.update(recursive_external)

    return local_deps, external_deps

# --- Project Exporter ---
def export_project(recipe_path: Path, local_deps: Set[Path], external_deps: Set[str]):
    recipe_name = recipe_path.stem
    export_path = EXPORTED_PROJECTS_DIR / recipe_name
    if export_path.exists():
        shutil.rmtree(export_path)
    export_path.mkdir(parents=True)
    all_files_to_copy = {recipe_path}.union(local_deps)
    for file_path in all_files_to_copy:
        relative_path = file_path.relative_to(PROJECT_ROOT)
        destination_path = export_path / relative_path
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(file_path, destination_path)
    try:
        root_pyproject_toml = PROJECT_ROOT / "pyproject.toml"
        root_toml_data = toml.load(root_pyproject_toml)
        root_dependencies = root_toml_data.get("tool", {}).get("poetry", {}).get("dependencies", {})
        new_dependencies = {
            "python": root_dependencies.get("python", "^3.12"),
            "pydantic": root_dependencies.get("pydantic", "^2.0.0") # Always include pydantic for the runner
        }
        for dep in external_deps:
            if dep in root_dependencies:
                new_dependencies[dep] = root_dependencies[dep]
            else:
                # Auto-add new external dependencies with mapping using DependencyResolver
                package_name = dependency_resolver.resolve(dep)
                # Check if package_name is valid (not None)
                if package_name:
                    print(f"Compiler: Adding new dependency '{package_name} = *'")
                    new_dependencies[package_name] = "*"
                else:
                    print(f"Compiler: Ignoring dependency '{dep}' (Standard Library or Unresolved).")

        new_toml_data = {
            "tool": {
                "poetry": {
                    "name": recipe_name,
                    "version": "0.1.0",
                    "description": "A compiled recipe from Dev0.",
                    "authors": ["Dev0 Compilation Engine <dev0@example.com>"],
                    "packages": [{"include": "project"}],
                    "dependencies": new_dependencies
                }
            }
        }
        with open(export_path / "pyproject.toml", "w", encoding="utf-8") as f:
            toml.dump(new_toml_data, f)
    except FileNotFoundError:
        print("Warning: Root pyproject.toml not found. Skipping dependency export.")
    except Exception as e:
        print(f"An error occurred during pyproject.toml generation: {e}")
    runner_content = f'''
import sys
from pathlib import Path
from pydantic import BaseModel
sys.path.append(str(Path(__file__).parent))
original_recipe_path = Path("{recipe_path.relative_to(PROJECT_ROOT)}")
recipe_import_path = ".".join(original_recipe_path.with_suffix('').parts)
recipe_name = "{recipe_name}"
exec_globals = {{}}
try:
    # Case 1: execute + Input
    exec(f"from {{recipe_import_path}} import execute, Input as RecipeInput", exec_globals)
    entrypoint = exec_globals['execute']
    RecipeInput = exec_globals.get('RecipeInput', BaseModel)
    has_input = True
except ImportError:
    try:
        # Case 2: execute only (Input defaults to BaseModel)
        exec(f"from {{recipe_import_path}} import execute", exec_globals)
        entrypoint = exec_globals['execute']
        RecipeInput = BaseModel
        has_input = False
    except ImportError:
        # Case 3: main
        exec(f"from {{recipe_import_path}} import main", exec_globals)
        entrypoint = exec_globals['main']
        has_input = False
import asyncio
import inspect

async def main_async():
    print(f"Executing recipe: {{recipe_name}}")
    try:
        if has_input:
            # Always create the Input model without arguments for simplicity
            input_data = RecipeInput()
            if isinstance(input_data, BaseModel):
                print(f"Using default input: {{input_data.model_dump_json(indent=2)}}")
            else:
                print(f"Using default input: {{input_data}}")

            if inspect.iscoroutinefunction(entrypoint):
                output = await entrypoint(input_data)
            else:
                output = entrypoint(input_data)
        else:
            if inspect.iscoroutinefunction(entrypoint):
                output = await entrypoint()
            else:
                output = entrypoint()

        print("\\n--- Recipe Output ---")
        if isinstance(output, BaseModel):
            print(output.model_dump_json(indent=2))
        else:
            print(output)
        print("--- End of Output ---\\n")
    except Exception as e:
        print(f"An error occurred: {{e}}")
        print("Please provide the required inputs as command-line arguments or a config file.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main_async())
'''
    with open(export_path / "run.py", "w", encoding="utf-8") as f:
        f.write(runner_content)

def execute(input_data: CompileProjectInput) -> CompileProjectOutput:
    recipe_filepath = Path(input_data.recipe_filepath)
    if not recipe_filepath.exists():
        raise FileNotFoundError(f"Recipe file not found: {recipe_filepath}")
    local_deps, external_deps = analyze_dependencies(recipe_filepath)
    export_project(recipe_filepath, local_deps, external_deps)
    export_path = EXPORTED_PROJECTS_DIR / recipe_filepath.stem
    return CompileProjectOutput(
        message=f"Project '{recipe_filepath.stem}' compiled successfully with {len(local_deps)} dependencies.",
        export_path=str(export_path)
    )
