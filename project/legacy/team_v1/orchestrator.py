"""
Orchestrator Agent (TEAM Mode): Manages the agentic software development workflow.

This module is the core of the TEAM mode. It orchestrates a linear, multi-agent
workflow to complete a development task from scratch.
"""
import asyncio
import json
from pydantic import BaseModel, Field
from typing import Optional

from project.recipes.agents.decomposer import execute_async as decomposer_execute_async
from project.recipes.agents.engineer import execute_async as engineer_execute_async
from project.recipes.agents.tester import execute_async as tester_execute_async, AgentTesterInput
from project.core.stitcher import stitch_decorators
from project.core.notebook import ModuleSpec

class Input(BaseModel):
    task_prompt: str

class Output(BaseModel):
    status: str
    message: str
    generated_code: Optional[str] = None
    test_code: Optional[str] = None

async def execute_async(input_data: Input) -> Output:
    """
    Asynchronously orchestrates the multi-agent workflow in a linear fashion.
    """
    print("--- Phase: Decomposition ---")
    # Прямой асинхронный вызов, без вложенных event loops
    decomposer_output_str = await decomposer_execute_async(input_data.task_prompt)
    decomposer_output = json.loads(decomposer_output_str)

    if "error" in decomposer_output or not decomposer_output.get("module_specs"):
        return Output(status="error", message=f"Decomposition failed: {decomposer_output.get('error', 'No specs generated.')}")

    module_spec_data = decomposer_output["module_specs"][0]
    module_spec = ModuleSpec(**module_spec_data)

    print(f"--- Phase: Engineering for module '{module_spec.name}' ---")

    engineer_input_spec = {
        "name": module_spec.name,
        "interface": module_spec.interface,
        "description": module_spec.description
    }
    engineer_output_str = await engineer_execute_async(json.dumps(engineer_input_spec))
    if "ERROR" in engineer_output_str:
        return Output(status="error", message=f"Engineering failed: {engineer_output_str}")

    engineer_output = json.loads(engineer_output_str)
    clean_code = engineer_output["final_code"]

    print(f"--- Phase: Stitching for module '{module_spec.name}' ---")
    try:
        stitched_code = stitch_decorators(source_code=clean_code, properties=module_spec.properties)
        print("Stitching successful. Code has been enhanced with architectural decorators.")
    except Exception as e:
        return Output(status="error", message=f"Stitching failed: {e}")

    print(f"--- Phase: Testing for module '{module_spec.name}' ---")

    tester_spec = {
        "name": module_spec.name,
        "description": module_spec.description,
        "code": stitched_code
    }
    tester_input = AgentTesterInput(task_string=json.dumps(tester_spec))
    tester_output_str = await tester_execute_async(tester_input)

    if "ERROR" in tester_output_str:
        return Output(status="error", message=f"Testing failed: {tester_output_str}", generated_code=stitched_code)

    tester_output = json.loads(tester_output_str)
    test_code = tester_output["final_test_code"]

    print("--- Orchestration Complete ---")
    return Output(
        status="success",
        message="Project successfully orchestrated through all phases.",
        generated_code=stitched_code,
        test_code=test_code
    )

def execute(input_data: Input) -> Output:
    """Synchronous wrapper for the async execute function."""
    return asyncio.run(execute_async(input_data))
