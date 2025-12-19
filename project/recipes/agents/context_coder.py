"""
Context Coder Agent: Writes code based strictly on provided research context.
"""
import asyncio
import json
import re
from pydantic import BaseModel, Field
from typing import Optional

from project.core.llm_gateway.gateway import execute as gateway_execute
from project.core.memory.qdrant_manager import get_qdrant_manager, COLLECTION_CODEBASE, COLLECTION_DOCUMENTATION

class ContextCoderInput(BaseModel):
    task_prompt: str
    research_context: str
    model_group: Optional[str] = Field("classic_coding", description="Model group to use.")

class ContextCoderOutput(BaseModel):
    # REMOVED filename to simplify model task
    pure_code: str = Field(..., description="The complete, executable Python code.")

async def execute_async(input_data: ContextCoderInput) -> ContextCoderOutput:
    """
    Generates code using research context to prevent hallucinations.
    Refactored for Direct Code Generation (no wrapper scripts).
    Simplified: Returns ONLY code. Filename is handled by Orchestrator.
    """
    try:
        with open("modules_db.json", "r", encoding="utf-8") as f:
            available_blocks = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        available_blocks = []
    blocks_json_str = json.dumps(available_blocks, indent=2)

    # --- Auto-Context RAG ---
    qm = get_qdrant_manager()
    code_chunks = qm.search_items(COLLECTION_CODEBASE, input_data.task_prompt, limit=5)
    doc_chunks = qm.search_items(COLLECTION_DOCUMENTATION, input_data.task_prompt, limit=3)

    rag_content = ""
    if code_chunks:
        rag_content += "\n**Reference Code (Project Style & Examples):**\n"
        for chunk in code_chunks:
            rag_content += f"---\nFile: {chunk.get('filepath')}\nContent:\n{chunk.get('content')}\n---\n"

    if doc_chunks:
        rag_content += "\n**Reference Documentation:**\n"
        for chunk in doc_chunks:
            rag_content += f"---\nFile: {chunk.get('filepath')}\nContent:\n{chunk.get('content')}\n---\n"
    # ------------------------

    prompt = f"""
You are a Senior Python Developer.
Your task is to write the **Source Code** for a single Python file that solves the user's request.

**CRITICAL INSTRUCTIONS:**
1. **Fail Loudly:** DO NOT wrap your main logic in `try...except` blocks that swallow errors. Let the script CRASH if something goes wrong.
2. **Requirements Definition:** If you use external libraries, YOU MUST list the *package names* in the module docstring.
   - Example: `\"\"\"\nRequirements: pypng, pyqrcode\n\"\"\"`
   - This is crucial for libraries where the package name differs from the import (e.g. `import png` -> `pypng`, `import cv2` -> `opencv-python`).

**User Task:** "{input_data.task_prompt}"

**CRITICAL: You must use the provided Research Context.**
Do not guess library methods. Use the cheat sheet below.

**Research Context (Cheat Sheet):**
{input_data.research_context}

{rag_content}

**Available Building Blocks (System Tools):**
{blocks_json_str}

**Strict Import Rules for Project Modules:**
If you use a module from `Available Building Blocks` (e.g., `project.modules...`), you MUST:
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
1.  **Structure:** You MUST wrap your logic in a `def main():` function.
    - Add `if __name__ == '__main__': main()` at the end.
2.  **Code:** Write the complete, working Python code.
    - **DO NOT** write a script that uses `create_file` to generate this code.
    - **DO NOT** wrap the code in triple quotes.
    - Just write the actual code that needs to run.
3.  **Imports:** Ensure all imports are correct based on the context.

**Output Format:**
Return ONLY the Python code wrapped in a markdown block.

**Example Output:**
```python
import requests

def execute():
    print("Hello")
```
"""
    model_group = input_data.model_group if input_data.model_group else "classic_coding"
    raw_response = await gateway_execute(model_group=model_group, prompt=prompt)

    # Parsing Strategy: Extract content from ```python ... ``` block
    code_block_match = re.search(r'```python(.*?)```', raw_response, re.DOTALL)
    if code_block_match:
        clean_code = code_block_match.group(1).strip()
        return ContextCoderOutput(pure_code=clean_code)

    # Fallback: Look for any code block
    code_block_match = re.search(r'```(.*?)```', raw_response, re.DOTALL)
    if code_block_match:
         clean_code = code_block_match.group(1).strip()
         if "import" in clean_code or "def " in clean_code:
             return ContextCoderOutput(pure_code=clean_code)

    if "def execute" in raw_response:
        return ContextCoderOutput(pure_code=raw_response.strip())

    raise ValueError(f"Could not parse Python code from ContextCoder. Response: {raw_response[:200]}...")

def execute(input_data: ContextCoderInput) -> ContextCoderOutput:
    return asyncio.run(execute_async(input_data))
