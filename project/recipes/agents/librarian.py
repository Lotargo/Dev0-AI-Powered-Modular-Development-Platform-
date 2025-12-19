"""
Librarian Agent: Manages self-learning via Vector DB and Cohere RAG.
"""
import asyncio
import uuid
import json
import re
from pydantic import BaseModel, Field
from typing import Optional

from project.core.llm_gateway.gateway import execute as gateway_execute
from project.modules.memory.vector_db import execute as vector_db_execute, VectorDBInput
from project.core.memory.qdrant_manager import get_qdrant_manager, COLLECTION_EXPERIENCES

class LibrarianInput(BaseModel):
    mode: str = Field(..., description="'recall' or 'store'")
    task_prompt: str
    outcome: Optional[str] = None
    execution_log: Optional[str] = None

class LibrarianOutput(BaseModel):
    briefing: str = Field("", description="Synthesized knowledge or confirmation message.")

async def execute_async(input_data: LibrarianInput) -> LibrarianOutput:
    # Use the dedicated Cohere RAG group
    model_group = "librarian_group"

    qm = get_qdrant_manager()

    if input_data.mode == "recall":
        # 1. Query VectorDB (Cascading Memory Logic)
        # We access QdrantManager directly to get Scores
        scored_items = qm.search_items(
            collection_name=COLLECTION_EXPERIENCES,
            query=input_data.task_prompt,
            limit=3
        )

        if not scored_items:
            return LibrarianOutput(briefing="No specific previous lessons found.")

        # 2. Golden Lesson Extraction (Cascading Step)
        golden_lesson = ""
        golden_code = ""

        # Threshold for "Golden" match
        SCORE_THRESHOLD = 0.80

        high_confidence_items = [item for item in scored_items if item.score > SCORE_THRESHOLD]

        if high_confidence_items:
            # Pick the best one
            best_item = high_confidence_items[0]

            # Check if it has structured data
            if "solution_code" in best_item and best_item["solution_code"]:
                golden_code = best_item["solution_code"]
                golden_lesson = best_item.get("key_insight", best_item.get("content", ""))

        # 3. Synthesize
        context_str = "\n".join([f"- {item.get('content', '')}" for item in scored_items])

        # If we found a Golden Lesson, we enforce it strictly.
        if golden_code:
             briefing = f"""
*** GOLDEN LESSON FOUND ***
The system has solved this EXACT task before. You MUST use the following solution pattern:

**Key Insight:** {golden_lesson}

**Required Code Pattern:**
```python
{golden_code}
```

**Instructions:**
Adapt the code above to the current task arguments. Do NOT deviate from the imports or logic shown.
"""
        else:
            # Standard RAG Synthesis
            prompt = f"""
You are the Project Librarian. You have retrieved the following lessons from the Knowledge Base:

{context_str}

**Current Task:** "{input_data.task_prompt}"

**Instructions:**
Synthesize these lessons into a concise "Mission Briefing" for the Planner and Coder.
Focus on pitfalls to avoid and patterns to use.
If the lessons are strictly irrelevant, simply state that.
"""
            briefing = await gateway_execute(model_group=model_group, prompt=prompt)

        return LibrarianOutput(briefing=briefing)

    elif input_data.mode == "store":
        # 1. Extract Structured Lesson
        log_content = input_data.execution_log or "No log provided."

        # Prompt for structured extraction
        prompt = f"""
You are the Project Librarian. Analyze the recent task execution to create a Structured Experience.

**Task:** "{input_data.task_prompt}"
**Outcome:** {input_data.outcome}
**Log Summary:**
{log_content[:3000]}... (truncated)

**Instructions:**
Extract the following fields in JSON format:
1. "key_insight": A concise, one-sentence rule (e.g. "Use Pillow instead of PIL").
2. "problem_summary": What went wrong or what was the challenge.
3. "solution_code": The EXACT minimal code snippet (imports + logic) that fixed it. NOT a full script, just the core logic.

**Format:**
Return ONLY a valid JSON object.
{{
  "key_insight": "...",
  "problem_summary": "...",
  "solution_code": "..."
}}
"""
        try:
            response = await gateway_execute(model_group=model_group, prompt=prompt)
            # Clean JSON
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
            else:
                data = {
                    "key_insight": response,
                    "problem_summary": "Unstructured",
                    "solution_code": ""
                }
        except Exception as e:
            print(f"Librarian: JSON parsing failed ({e}). Storing as text.")
            data = {
                "key_insight": "Failed to extract structured lesson.",
                "problem_summary": str(e),
                "solution_code": ""
            }

        # 2. Store Structured Data
        # We store the 'key_insight' as the main text content for semantic search,
        # and the rest as metadata.
        qm.add_item(
            collection_name=COLLECTION_EXPERIENCES,
            text=data["key_insight"], # This is what we embed!
            metadata={
                "task": input_data.task_prompt,
                "outcome": input_data.outcome or "unknown",
                "problem_summary": data["problem_summary"],
                "solution_code": data["solution_code"],
                "is_structured": True
            },
            item_id=str(uuid.uuid4())
        )

        return LibrarianOutput(briefing=f"Stored structured lesson: {data['key_insight']}")

    return LibrarianOutput(briefing="Invalid mode.")

def execute(input_data: LibrarianInput) -> LibrarianOutput:
    return asyncio.run(execute_async(input_data))
