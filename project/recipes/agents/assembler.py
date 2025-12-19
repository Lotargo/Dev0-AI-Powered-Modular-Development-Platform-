"""
Assembler Agent (Classic Mode): Writes standard Python code based on a strategic plan.
"""
import asyncio
import json
import re
from pydantic import BaseModel, Field
from typing import Optional

from project.core.llm_gateway.gateway import execute as gateway_execute

class AssemblerInput(BaseModel):
    task_prompt: str
    plan: str
    feedback: Optional[str] = Field(None, description="Feedback from a previous failed run.")
    model_group: Optional[str] = Field("coding_model_group", description="The model group to use.")

class AssemblerOutput(BaseModel):
    filename: str = Field(..., description="The suggested filename for the code.")
    pure_code: str = Field(..., description="The complete, executable Python code.")

async def execute_async(input_data: AssemblerInput) -> AssemblerOutput:
    """
    Takes a plan and generates the corresponding Python code.
    Now simplified: It generates the *target code directly*, not a script to create it.
    """

    # Tool RAG: Search for relevant tools using Qdrant
    try:
        from project.core.memory.qdrant_manager import get_qdrant_manager
        qm = get_qdrant_manager()
        # Query with task + plan for context
        query = f"{input_data.task_prompt}\n{input_data.plan}"
        available_blocks = qm.search_tools(query, limit=10)
    except Exception as e:
        # Fallback or empty if RAG fails (should not happen in stable env)
        print(f"Warning: Tool RAG failed ({e}). Tools will be unavailable.")
        available_blocks = []

    blocks_json_str = json.dumps(available_blocks, indent=2)

    feedback_section = ""
    if input_data.feedback:
        feedback_section = f"""
**IMPORTANT - Previous Attempt Failed:**
Your last generated code failed with the following error. Analyze this feedback carefully and generate a corrected version.

**Feedback:**
```
{input_data.feedback}
```
"""

    # Check for GOLDEN LESSON in task prompt (Librarian injects it there)
    golden_lesson_section = ""
    if "*** GOLDEN LESSON FOUND ***" in input_data.task_prompt:
         golden_lesson_section = """
*** CRITICAL INSTRUCTION ***
The Librarian has identified a PROVEN solution (GOLDEN LESSON) in the task description above.
You MUST follow the code pattern provided in the Golden Lesson EXACTLY.
Do not reinvent the wheel. Adapt the proven code to the specific variable names required, but keep the imports and logic identical.
"""

    prompt = f"""
You are a pragmatic Python Assembler.
Your goal is to write the **Source Code** for a single Python file that solves the user's problem based on the plan.

**User's Task & Context:**
"{input_data.task_prompt}"

**Strategic Plan:**
"{input_data.plan}"

{golden_lesson_section}

**Context:**
- You are writing the *actual file content*.
- **DO NOT** write a script that uses `create_file` or `open(..., 'w')` to generate the code.
- **DO NOT** wrap the code in triple quotes unless it's a docstring.
- Just write the pure Python code that does the job.

**Available Libraries:**
You can import and use these system modules if needed (e.g. for file I/O, system commands):
```json
{blocks_json_str}
```

**Strict Import Rules for Project Modules:**
If you use a module from `Available Libraries` (e.g., `project.modules...`), you MUST:
1. Import the `execute` function and alias it (e.g., `from ... import execute as create_file_exec`).
2. Import the specific Input Model class found in the `schemas.Input.class_name` field (e.g., `CreateFileInput`).
3. Instantiate the Input Model with keyword arguments.
4. Pass the model instance to the execute function.

**WRONG:**
`from project.modules.filesystem.create_file import create_file` -> `create_file({{'path': ...}})` (This fails because you are calling a module with a dict!)

**CORRECT:**
```python
from project.modules.filesystem.create_file import execute as create_file_exec, CreateFileInput
create_file_exec(CreateFileInput(path="file.txt", content="hello"))
```

**Instructions:**
1. **Filename:** Decide on a descriptive filename (e.g., `data_processor.py`).
2. **Structure:** You MUST wrap your logic in a `def main():` function.
   - Add `if __name__ == '__main__': main()` at the end.
   - **DO NOT** write top-level executable code outside of functions.
3. **Code:** Write the complete, working Python code.
   - It should be a standalone script.
   - It can use standard libraries or the provided project modules.

{feedback_section}

**Output Format:**
Return ONLY the Python code wrapped in a markdown block.
The FIRST line of the code MUST be a comment with the filename.

**Example Output:**
```python
# filename: hello_world.py
import os

def main():
    print('Hello World')

if __name__ == '__main__':
    main()
```
"""
    group_to_use = input_data.model_group if input_data.model_group else "coding_model_group"
    raw_response = await gateway_execute(model_group=group_to_use, prompt=prompt)

    # Parsing Strategy: Extract content from ```python ... ``` block
    code_block_match = re.search(r'```python(.*?)```', raw_response, re.DOTALL)
    clean_code = ""
    if code_block_match:
        clean_code = code_block_match.group(1).strip()
    else:
        # Fallback: Look for any code block
        code_block_match = re.search(r'```(.*?)```', raw_response, re.DOTALL)
        if code_block_match:
             clean_code = code_block_match.group(1).strip()
        elif "def main" in raw_response:
             clean_code = raw_response.strip()

    if not clean_code:
        raise ValueError(f"Could not parse Python code from Assembler response. Response: {raw_response[:200]}...")

    # Extract filename from comment
    filename_match = re.search(r'^#\s*filename:\s*(.*)', clean_code, re.MULTILINE)
    filename = "recipe_generated.py"
    if filename_match:
        filename = filename_match.group(1).strip()

    return AssemblerOutput(filename=filename, pure_code=clean_code)

def execute(input_data: AssemblerInput) -> AssemblerOutput:
    return asyncio.run(execute_async(input_data))
