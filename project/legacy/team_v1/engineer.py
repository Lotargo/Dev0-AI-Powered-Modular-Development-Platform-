"""
Engineer Agent: Takes a module specification and generates the corresponding Python code.
"""
import json
import re
import asyncio
from pydantic import BaseModel

from project.core.llm_gateway.gateway import execute as gateway_execute

class Input(BaseModel):
    module_spec: str  # JSON string of the ModuleSpec

class Output(BaseModel):
    final_code: str

def _parse_response(response_text: str) -> str:
    """Extracts the Python code block from the LLM's response."""
    match = re.search(r'```python\n(.*?)```', response_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return response_text.strip()

async def execute_async(module_spec_json: str) -> str:
    """
    Asynchronously takes a module specification and generates the Python code.
    """
    spec = json.loads(module_spec_json)
    prompt = f"""
You are an expert Python programmer. Your task is to write clean, efficient, and correct Python code for a given module specification.

**Module Specification:**
```json
{json.dumps(spec, indent=2)}
```

**CRITICAL INSTRUCTIONS:**
1.  **IMPLEMENT BUSINESS LOGIC ONLY:** Write only the core logic.
2.  **DO NOT ADD DECORATORS:** You must not add any decorators (like `@atomic`). The system will do this automatically.
3.  **STRICTLY ADHERE TO THE INTERFACE:**
    *   The function signature must exactly match the `input` and `output` specifications.
    *   The function **MUST** be named `execute`.
    *   Use Pydantic models for input and output types.
4.  **INCLUDE IMPORTS & PYDANTIC MODELS:** The generated code must include all necessary imports (`pydantic.BaseModel`) and the full definition for the `Input` and `Output` Pydantic classes.
5.  **PYTHON CODE BLOCK ONLY:** Your final output must be a single Python code block. Do not add any commentary or explanation.

**Example Output:**
```python
from pydantic import BaseModel

class Input(BaseModel):
    num1: int
    num2: int

class Output(BaseModel):
    sum: int

def execute(data: Input) -> Output:
    result = data.num1 + data.num2
    return Output(sum=result)
```
"""
    # Engineer is a coding-heavy task
    generated_text = await gateway_execute(model_group="coding_model_group", prompt=prompt)

    try:
        final_code = _parse_response(generated_text)
        # Simple validation: check if 'def execute' is in the code
        if "def execute" not in final_code:
            raise ValueError("Generated code does not contain an 'execute' function.")

        output = Output(final_code=final_code)
        return output.model_dump_json()
    except (ValueError) as e:
        return json.dumps({"ERROR": str(e), "final_code": ""})

def execute(module_spec_json: str) -> str:
    return asyncio.run(execute_async(module_spec_json))
