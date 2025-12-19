"""
Decomposer Agent: Breaks down a strategic plan into actionable, atomic module specifications.
"""
import json
import re
import asyncio
from pydantic import BaseModel, ValidationError
from typing import List

from project.core.llm_gateway.gateway import execute as gateway_execute
from project.core.notebook import ModuleSpec

class Input(BaseModel):
    strategic_plan: str

class Output(BaseModel):
    module_specs: List[ModuleSpec]

def _parse_response(response_text: str) -> dict:
    """Extracts the JSON block from the LLM's response."""
    match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        json_str = response_text

    try:
        # The output is a list, not a dictionary, so we load it directly
        return {"module_specs": json.loads(json_str)}
    except json.JSONDecodeError:
        raise ValueError("Failed to decode JSON from LLM response.")

async def execute_async(task: str) -> str:
    """
    Asynchronously takes a high-level strategic plan and decomposes it into a list of
    ModuleSpec objects.
    """
    prompt = f"""
You are a Pragmatic Senior Software Engineer. Your job is to break down a user's request into the absolute minimum number of implementable Python modules required to solve the core problem.

**The Goal:** "{task}"

**CRITICAL RULES:**
1.  **MINIMALISM IS KEY:** Your primary goal is to find the most direct path to a working solution. For most tasks, this will be **ONE** single module. Do not exceed two modules unless absolutely necessary.
2.  **FOCUS ON CORE LOGIC:** You must ONLY define modules that implement the central business logic. AVOID boilerplate like CLIs, config loaders, etc.
3.  **ARCHITECTURAL PROPERTIES:** For each module, you MUST specify its architectural properties. For now, every module you create must have the `"atomic"` property to register it with the system.
    *   `"atomic"`: Marks the module as a fundamental, reusable building block.
4.  **CONCRETE & IMPLEMENTABLE:** Each module must be a tangible piece of Python code.
5.  **JSON OUTPUT ONLY:** Your final output MUST be a raw JSON array of module specification objects. Do not add any commentary. Each object must contain `name`, `interface`, `description`, and `properties`.

**Example for "Create a QR code from a URL and save it":**
```json
[
  {{
    "name": "qr_code_generator",
    "interface": {{
      "input": "url: str, file_path: str",
      "output": "success: bool"
    }},
    "description": "Takes a string URL and a file path, generates a QR code, and saves it as an image to the specified path. Returns True on success.",
    "properties": ["atomic"]
  }}
]
```
"""
    # Decomposer is a reasoning-heavy task
    generated_text = await gateway_execute(model_group="reasoning_model_group", prompt=prompt)

    try:
        parsed_json_data = _parse_response(generated_text)
        validated_output = Output(**parsed_json_data)
        return validated_output.model_dump_json()
    except (ValueError, ValidationError) as e:
        error_message = f"Failed to generate valid module specifications. Error: {e}"
        return json.dumps({"error": error_message, "module_specs": []})

def execute(task: str) -> str:
    return asyncio.run(execute_async(task))
