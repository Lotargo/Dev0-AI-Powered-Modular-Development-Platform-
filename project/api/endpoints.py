"""This module defines the API endpoints for the application.
It provides endpoints for listing available tools, executing a module,
getting the source code of a module, and rescanning the module registry.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from pydantic import ValidationError

from project.core.module_registry import module_registry

router = APIRouter()


@router.post("/v1/modules/execute/{module_name}")
async def execute_module(module_name: str, inputs: Dict[str, Any]):
    """Executes a module by its name.
    Args:
        module_name: The name of the module to execute.
        inputs: A dictionary of inputs for the module.
    Returns:
        A dictionary with the result of the module execution.
    Raises:
        HTTPException: If the module is not found or the inputs are invalid.
    """
    module = module_registry.get_module(module_name)
    if not module:
        raise HTTPException(status_code=404, detail=f"Module {module_name} not found")

    try:
        input_model = module["input_model"]
        validated_inputs = input_model(**inputs)
        result = module["execute"](validated_inputs)
        return {
            "module": module_name,
            "success": True,
            "result": result.model_dump(),
        }
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid inputs: {e}")


@router.get("/v1/modules/source/{module_name}", response_model=Dict[str, str])
async def get_module_source(module_name: str):
    """Returns the source code of a specific module.
    Args:
        module_name: The name of the module.
    Returns:
        A dictionary with the module name and its source code.
    Raises:
        HTTPException: If the module is not found or the source code cannot
        be read.
    """
    filepath = module_registry.get_module_filepath(module_name)
    if not filepath:
        raise HTTPException(status_code=404, detail=f"Module {module_name} not found")

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source_code = f.read()
        return {"module_name": module_name, "source_code": source_code}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not read module source: {e}")


@router.post("/v1/registry/rescan", response_model=Dict[str, Any])
async def rescan_modules():
    """Triggers a re-scan of all module directories.
    This endpoint allows you to discover new modules without restarting the
    application.
    Returns:
        A dictionary with the status of the operation.
    Raises:
        HTTPException: If the rescan fails.
    """
    try:
        module_registry.rescan_modules()
        new_tool_count = len(module_registry.list_tools())
        return {"status": "success", "message": f"Module registry refreshed. Found {new_tool_count} tools."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rescan modules: {e}")
