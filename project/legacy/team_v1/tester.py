"""
Tester Agent: Takes a module's code and specification, and generates pytest tests.
"""
import json
import re
import asyncio
from pydantic import BaseModel

from project.core.llm_gateway.gateway import execute as gateway_execute

class AgentTesterInput(BaseModel):
    task_string: str

class Output(BaseModel):
    final_test_code: str

def _parse_response(response_text: str) -> str:
    """Extracts the Python code block from the LLM's response."""
    match = re.search(r'```python\n(.*?)```', response_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return response_text.strip()

async def execute_async(input_data: AgentTesterInput) -> str:
    """
    Asynchronously takes a module's code and spec, and generates pytest tests.
    """
    spec = json.loads(input_data.task_string)
    prompt = f"""
You are a meticulous Test Engineer. Your task is to write comprehensive pytest tests for a given Python module.

**Module Specification & Code:**
```json
{json.dumps(spec, indent=2)}
```

**CRITICAL INSTRUCTIONS:**
1.  **IMPORT CORRECTLY:** The module to be tested is not yet in a package. You must import the `execute` function and its Pydantic models from a temporary file. A special utility `load_module_from_code` will be used by the test runner. You **MUST** write the import statement exactly like this:
    ```python
    from project.core.test_utils import load_module_from_code
    module = load_module_from_code('''
    {spec['code']}
    ''')
    execute = module.execute
    Input = module.Input
    Output = module.Output
    ```
2.  **WRITE ROBUST TESTS:** Cover the main success path and at least one edge case (e.g., invalid input).
3.  **USE `pytest`:** The tests must be written for the pytest framework.
4.  **PYTHON CODE BLOCK ONLY:** Your final output must be a single Python code block containing the complete test file.

**Example Output:**
```python
import pytest
from project.core.test_utils import load_module_from_code

# The test runner will replace this with the actual code
module_code = '''
{spec['code']}
'''
module = load_module_from_code(module_code)
execute = module.execute
Input = module.Input
Output = module.Output

def test_success_case():
    # Test logic here
    pass

def test_edge_case():
    # Test logic here
    pass
```
"""
    # Tester is a coding-heavy task
    generated_text = await gateway_execute(model_group="coding_model_group", prompt=prompt)

    try:
        final_test_code = _parse_response(generated_text)
        # Simple validation
        if "def test_" not in final_test_code:
            raise ValueError("Generated code does not contain any pytest tests.")

        output = Output(final_test_code=final_test_code)
        return output.model_dump_json()
    except (ValueError) as e:
        return json.dumps({"ERROR": str(e), "final_test_code": ""})

def execute(input_data: AgentTesterInput) -> str:
    return asyncio.run(execute_async(input_data))
