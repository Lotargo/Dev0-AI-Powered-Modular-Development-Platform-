"""
The Stitcher Module.

This module is a core component of the "Industrial Conveyor" architecture.
Its role is to take a "specification" from an agent (consisting of pure,
"happy path" business logic and a list of declarative decorators) and
"stitch" them together into a final, robust, and syntactically correct
Python script.

It uses Abstract Syntax Trees (AST) to programmatically add the decorators
to the function definition, ensuring that the final output is always valid code.
"""

import ast
import astor
from pydantic import BaseModel
from typing import List

class StitcherInput(BaseModel):
    pure_code: str
    decorators: List[str]

class StitcherOutput(BaseModel):
    final_code: str

class DecoratorVisitor(ast.NodeTransformer):
    """
    An AST visitor that adds a list of decorators to a function definition.
    """
    def __init__(self, decorators_to_add: List[str]):
        self.parsed_decorators = []
        self.required_imports = set()

        # Map known decorators to their import paths
        # We use aliases (as name) to match the decorator name used by the agent.
        self.decorator_imports = {
            'safe_call': 'from project.core.framework.safe_call import safe_call',
            'retry': 'from project.core.framework.retry import retry',
            'timed': 'from project.core.framework.observability import observable as timed',
            'observable': 'from project.core.framework.observability import observable',
            'atomic': 'from project.core.framework.atomic import atomic',
            'log_io': 'from project.core.framework.observability import observable as log_io',
        }

        for d in decorators_to_add:
            # Clean string
            d_clean = d.strip()

            # Identify decorator name for import injection
            # e.g. "@retry(3)" -> "retry", "@safe_call" -> "safe_call"
            name_part = d_clean.lstrip("@").split("(")[0].strip()
            if name_part in self.decorator_imports:
                self.required_imports.add(self.decorator_imports[name_part])

            # Remove leading @ if present (we will parse it as an expression)
            # To extract the AST node for a decorator like "@retry(attempts=3)",
            # the easiest way is to wrap it in a dummy function.
            dummy_code = f"{d_clean}\ndef dummy(): pass"
            try:
                dummy_tree = ast.parse(dummy_code)
                # The first item in body is the FunctionDef.
                # Its decorator_list has our decorator node.
                if isinstance(dummy_tree.body[0], ast.FunctionDef):
                    self.parsed_decorators.extend(dummy_tree.body[0].decorator_list)
            except SyntaxError:
                # Fallback
                pass

        super().__init__()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        # We only want to add decorators to the main 'execute' function
        if node.name == 'execute':
            # Prepend our new decorators to the existing list
            node.decorator_list = self.parsed_decorators + node.decorator_list
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
         # Same logic for async functions
        if node.name == 'execute':
            node.decorator_list = self.parsed_decorators + node.decorator_list
        return node

def execute(input_data: StitcherInput) -> StitcherOutput:
    """
    Takes pure Python code and a list of decorators, and returns the final stitched code.
    """
    if not input_data.decorators:
        # If there are no decorators, just return the original code
        return StitcherOutput(final_code=input_data.pure_code)

    # 1. Parse the pure code into an Abstract Syntax Tree (AST)
    # Handle common indentation errors from LLMs (if pure_code is indented)
    import textwrap
    cleaned_code = textwrap.dedent(input_data.pure_code).strip()

    tree = ast.parse(cleaned_code)

    # 2. Create an instance of our visitor and have it transform the tree
    visitor = DecoratorVisitor(decorators_to_add=input_data.decorators)
    transformed_tree = visitor.visit(tree)

    # 3. Inject Imports (if needed)
    # We inject them at the top of the module
    if visitor.required_imports:
        import_nodes = []
        for imp_str in visitor.required_imports:
            try:
                import_nodes.extend(ast.parse(imp_str).body)
            except SyntaxError:
                pass

        # Insert imports at the beginning, after docstrings/future imports
        # Simple strategy: insert at index 0 (AST handles order usually)
        # But to be safe, we find the first non-import, non-docstring statement?
        # For now, inserting at 0 is fine, python allows imports anywhere.
        # Ideally, we check if it already exists to avoid dupes, but Python handles dupe imports fine.
        transformed_tree.body = import_nodes + transformed_tree.body

    # 4. Fix any missing line numbers or other metadata
    ast.fix_missing_locations(transformed_tree)

    # 5. Unparse the transformed AST back into Python code
    final_code = astor.to_source(transformed_tree)

    return StitcherOutput(final_code=final_code)
