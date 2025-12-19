"""
Planner Agent: Creates a high-level strategic plan.
"""
import asyncio
import json
from project.core.llm_gateway.gateway import execute as gateway_execute

async def execute_async(task: str, model_group: str = "reasoning_model_group") -> str:
    """
    Asynchronously takes a project goal and creates a high-level strategic plan.
    """

    # Tool RAG: Search for relevant tools using Qdrant
    try:
        from project.core.memory.qdrant_manager import get_qdrant_manager
        qm = get_qdrant_manager()
        available_blocks = qm.search_tools(task, limit=10)
    except Exception as e:
        print(f"Warning: Tool RAG failed in Planner ({e}).")
        available_blocks = []

    blocks_json_str = json.dumps(available_blocks, indent=2)

    prompt = f"""
You are a Senior Systems Architect.
Your task is to take a user's request and create a **detailed, step-by-step implementation plan** for a Junior Developer.

**User Request:** "{task}"

**Available Tools (Reference):**
These are the existing atomic blocks in the system. Prefer using them over custom scripts.
```json
{blocks_json_str}
```

**Guidelines for the Plan:**
1.  **Atomic Steps:** Break the task down into small, logical actions.
2.  **Explicit Operations:**
    *   If a file needs to be created, say "Create file 'filename.ext' with logic to..."
    *   If a directory is needed, say "Create directory 'path/to/dir'".
    *   If a script needs to be run, say "Execute 'filename.ext'".
3.  **Data Flow:** Mention what input each step needs and what output it produces.
4.  **Simplicity:** Keep the steps linear and clear.

**Output Format:**
Return **only** the numbered list of steps. Do not include introductory text.

**Example:**
1. Create a working directory at '/tmp/my_project'.
2. Create a file 'data_processor.py' that reads 'input.txt' and writes 'output.txt'.
3. Execute 'data_processor.py' using the python executor.
"""
    response = await gateway_execute(model_group=model_group, prompt=prompt)
    return response.strip()

def execute(task: str, model_group: str = "reasoning_model_group") -> str:
    """
    Synchronous wrapper for the async execute function.
    """
    return asyncio.run(execute_async(task, model_group=model_group))
