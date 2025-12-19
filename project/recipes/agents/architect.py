"""
Architect Agent (SOLO Mode): Creates a modular recipe by composing existing building blocks.
"""
import asyncio
import re
import json
from pydantic import BaseModel
import logging
import os

from project.core.llm_gateway.gateway import execute as gateway_execute
from project.modules.filesystem.create_file import execute as create_file, CreateFileInput
from project.core.framework.observability import observable

from pydantic import Field
from typing import Optional, List

class ArchitectInput(BaseModel):
    task_prompt: str
    feedback: Optional[str] = Field(None, description="Feedback from a previous failed run to inform the next attempt.")
    model_group: Optional[str] = Field("coding_model_group", description="The model group to use for generation.")

class ArchitectOutput(BaseModel):
    pure_code: str
    decorators: List[str]

@observable(source_name="ArchitectAgent")
async def execute_async(input_data: ArchitectInput) -> str:
    """
    Takes a task and generates a JSON specification string for a recipe.
    The parsing and validation of this string is the responsibility of the caller.
    """
    try:
        with open("modules_db.json", "r", encoding="utf-8") as f:
            available_blocks = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        available_blocks = []

    blocks_json_str = json.dumps(available_blocks, indent=2)

    feedback_section = ""
    if input_data.feedback:
        feedback_section = f"""
**IMPORTANT - Previous Attempt Failed:**
Your last generated recipe failed with the following error. Analyze this feedback carefully and generate a corrected, improved version of the code that fixes the issue.

**Feedback:**
```
{input_data.feedback}
```
"""

    prompt = f"""
You are a pragmatic and brilliant AI Architect. Your task is to generate a **specification** for a Python recipe that solves the user's request. This specification consists of two parts: the pure business logic and a list of decorators to enhance it.
{feedback_section}
**Your available building blocks (Knowledge Base):**
```json
{blocks_json_str}
```

**Available System Decorators (for enhancing the code):**
- `@safe_call`: Makes the function return a Result object instead of throwing an exception. Essential for any operation that might fail (e.g., file I/O, network requests).
- `@retry(attempts=3, delay=1)`: Automatically retries the function on failure.
- `@timed`: Logs the execution time of the function.
- `@log_io`: Logs the inputs and outputs of the function.

**User's Task:** "{input_data.task_prompt}"

**Critical Instructions:**
1.  **Step 1: Write the Pure Code.**
    *   Write a clean Python script that solves the task, focusing only on the "happy path".
    *   This code should be a single function named `execute`.
    *   **FILE PATHS:** You **MUST** use **relative paths** (e.g., `project/main.py`, `README.md`).
    *   **FORBIDDEN:** Do **NOT** use absolute paths (starting with `/` or `/app/`). Do **NOT** write to `/tmp` or `/app/project` directly. Always write relative to the project root.
    *   **IMPORTS:** Use explicit imports from the building blocks list. Check the `import_path` and `class_name` in the knowledge base.
    *   **DO NOT** include error handling or resilience patterns (these are for decorators).
2.  **Step 2: Select Decorators.**
    *   Analyze the pure code. Select decorators to make it robust (e.g., `@safe_call`, `@retry`).
3.  **Structure the Output.**
    *   Your final output **MUST** be a single, valid JSON object with keys `"pure_code"` and `"decorators"`.

**Example Output (Correct):**
```json
{{
  "pure_code": "from project.modules.filesystem.create_file import execute as create_file, CreateFileInput\\n\\nasync def execute():\\n    # Correct: Uses relative path\\n    create_file(CreateFileInput(path=\\"project/data/output.txt\\", content=\\"Result...\\"))",
  "decorators": ["@safe_call", "@timed"]
}}
```

**Example Output (INCORRECT - DO NOT DO THIS):**
```json
{{
  "pure_code": "... create_file(CreateFileInput(path=\\"/app/project/main.py\\", ...))",
  "decorators": [...]
}}
```

Your output **MUST** be only the raw JSON, with no other text.
"""
    # Use the provided model group or default
    group_to_use = input_data.model_group if input_data.model_group else "coding_model_group"
    llm_output = await gateway_execute(model_group=group_to_use, prompt=prompt)

    return llm_output


def execute(input_data: ArchitectInput) -> str:
    return asyncio.run(execute_async(input_data))
