import importlib
import inspect
from pathlib import Path
from typing import Dict, Any, List
from pydantic import BaseModel
from .contracts.base_module import ModuleV1


class ModuleRegistry:
    """Manages the discovery, registration, and retrieval of executable modules.
    This class scans predefined directories (`modules`, `adapters`, `recipes`) for valid
    module files, validates their structure and schemas, and stores them for later retrieval
    and execution. It provides methods to list all available modules and to get a specific
    module by its name.
    Attributes:
        _modules: A dictionary holding the registered modules, where the key is the
                  module name and the value is a dictionary of module metadata and
                  the executable function.
    """

    def __init__(self):
        """Initializes the ModuleRegistry with an empty module store."""
        self._modules: Dict[str, Dict[str, Any]] = {}

    def discover_and_register_modules(self):
        """Discovers and registers all valid modules.
        This method scans the `modules`, `adapters`, and `recipes` directories
        recursively for valid module files, validates them against the schema,
        and registers them in the `_modules` dictionary.
        """
        project_root = Path(__file__).parent.parent
        source_roots = ["modules", "adapters", "recipes"]

        for source in source_roots:
            source_path = project_root / source
            if not source_path.exists():
                continue

            for module_file in source_path.rglob("*.py"):
                if module_file.name != "__init__.py":
                    # Construct the import path relative to the 'project' directory
                    relative_path = module_file.relative_to(project_root)
                    module_path_parts = list(relative_path.parts)
                    module_path_parts[-1] = module_file.stem
                    module_path = "project." + ".".join(module_path_parts)

                    # Determine the category relative to the source root (e.g., 'modules', 'recipes')
                    category_path = module_file.relative_to(source_path).parent
                    category = str(category_path).replace("/", ".")
                    if category == ".":
                        category = source

                    self._try_register_module(module_path, module_file.stem, category)

    def _try_register_module(self, module_path: str, module_name: str, category: str):
        """Tries to register a single module, validating its structure and schema.
        This method attempts to import a module dynamically from the given source,
        category, and module name. It inspects the module for an `execute` function,
        infers the input and output Pydantic models from its signature, and validates
        the module's structure. If the module is valid, it's added to the registry.
        Args:
            module_path: The full import path to the module.
            module_name: The name of the module, corresponding to the Python filename.
            category: The category of the module, corresponding to the subdirectory.
        """
        try:
            module = importlib.import_module(module_path)

            execute_func = getattr(module, "execute", None)
            if not execute_func or not callable(execute_func):
                return

            sig = inspect.signature(execute_func)
            params = list(sig.parameters.values())
            if not params:
                return

            input_model = params[0].annotation
            output_model = sig.return_annotation

            if not (inspect.isclass(input_model) and issubclass(input_model, BaseModel) and
                    inspect.isclass(output_model) and issubclass(output_model, BaseModel)):
                return

            module_data = {
                "name": module_name,
                "description": inspect.getdoc(execute_func) or "",
                "category": category,
                "input_schema": input_model.model_json_schema(),
                "output_schema": output_model.model_json_schema(),
            }


            self._modules[module_name] = {
                **module_data,
                "execute": execute_func,
                "input_model": input_model,
            }
        except Exception as e:
            print(f"DEBUG: Failed to register module '{module_name}' from path '{module_path}': {e}")
            pass

    def list_tools(self) -> List[ModuleV1]:
        """Returns a list of all registered modules.
        This method returns a list of all registered modules, conforming to the
        ModuleV1 contract.
        Returns:
            A list of ModuleV1 objects.
        """
        return [ModuleV1(**meta) for meta in self._modules.values()]


    def get_module(self, module_name: str) -> Dict[str, Any]:
        """Retrieves a module by its name.
        Args:
            module_name: The name of the module to retrieve.
        Returns:
            A dictionary containing the module's metadata and executable function,
            or None if the module is not found.
        """
        return self._modules.get(module_name)

    def get_module_filepath(self, module_name: str) -> str | None:
        """Retrieves the absolute filepath for a given module name.
        Args:
            module_name: The name of the module.
        Returns:
            The absolute filepath of the module's source file, or None if the
            module is not found or the filepath cannot be determined.
        """
        module_info = self._modules.get(module_name)
        if not module_info:
            return None

        # This is a bit of a hack, but it's the most reliable way to get the path
        # from the function object.
        execute_func = module_info.get("execute")
        if not execute_func:
            return None

        return inspect.getfile(execute_func)

    def rescan_modules(self):
        """Clears the current module registry and re-discovers all modules.
        This method is useful when you have added new modules to the system
        and want to make them available without restarting the application.
        """
        self._modules = {}
        self.discover_and_register_modules()


# Global instance of the registry
module_registry = ModuleRegistry()
