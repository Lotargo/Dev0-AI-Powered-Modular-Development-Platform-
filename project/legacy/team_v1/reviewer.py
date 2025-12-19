"""
Reviewer Agent: Analyzes failed tests using LLM Function Calling to get structured output.
"""
import json
import asyncio
from pydantic import BaseModel, Field

from project.core.llm_gateway.gateway import generate_chat_completion
from project.core.llm_gateway.models import ChatCompletionRequest, Tool
from project.core.pydantic_to_json_schema import pydantic_to_json_schema

# --- Pydantic Models ---

class ReviewerInput(BaseModel):
    module_code: str = Field(..., description="The source code of the module being tested.")
    test_code: str = Field(..., description="The source code of the pytest test that failed.")
    pytest_output: str = Field(..., description="The full, raw output from the failed pytest execution.")

class ReviewerOutput(BaseModel):
    assign_to: str = Field(..., description="The agent to assign the fix to. Must be 'Engineer' or 'Tester'.")
    feedback: str = Field(..., description="Clear, concise, and actionable feedback for the assigned agent.")

# --- Core Reviewer Logic ---

async def execute_async(input_data: ReviewerInput) -> str:
    """
    Asynchronously analyzes a failed test and returns a structured JSON by leveraging function calling.
    """
    # 1. Create the JSON Schema for the tool
    reviewer_tool_schema = pydantic_to_json_schema(
        model=ReviewerOutput,
        function_name="record_triage_decision",
        function_description="Records the decision of the triage engineer, assigning a failed test to the correct agent with feedback."
    )

    prompt = f"""
You are an expert AI triage engineer. Your task is to analyze a failed test and determine whether the bug is in the application code or the test code itself. Then, you must call the `record_triage_decision` function to record your conclusion.

**CONTEXT:**
- The `Engineer` agent wrote the application code.
- The `Tester` agent wrote the test code.
- The test failed, and now you must decide who is responsible for fixing it.

**ANALYSIS MATERIAL:**

1.  **Application Code (`Engineer`):**
    ```python
    {input_data.module_code}
    ```

2.  **Test Code (`Tester`):**
    ```python
    {input_data.test_code}
    ```

3.  **Pytest Failure Log:**
    ```
    {input_data.pytest_output}
    ```

**YOUR TASK:**
1.  **Analyze the Root Cause:** Carefully examine all provided materials.
    - If the test logic is flawed, mocks are incorrect, or there's a syntax/import error in the test, the `Tester` is responsible.
    - If the application code has a bug that the test correctly identified, the `Engineer` is responsible.
2.  **CALL THE FUNCTION:** Based on your analysis, you **MUST** call the `record_triage_decision` function with the appropriate `assign_to` and `feedback` arguments.
"""

    for attempt in range(2): # Allow one retry
        request = ChatCompletionRequest(
            model="default_model_group",
            messages=[{"role": "user", "content": prompt}],
            tools=[Tool(**reviewer_tool_schema)],
            tool_choice="auto"
        )

        response = await generate_chat_completion(request)

        # Check if the model made a tool call
        if response.choices and response.choices[0].message.tool_calls:
            tool_call = response.choices[0].message.tool_calls[0]
            if tool_call.function.name == "record_triage_decision":
                # Success! Return the structured arguments.
                return tool_call.function.arguments

        # If no tool call was made, or the wrong one, we'll loop again.
        print(f"Attempt {attempt + 1}: LLM did not call the function correctly. Retrying...")

    # If we exit the loop, the agent has failed.
    # We return a default error JSON that assigns to the Engineer.
    return json.dumps({
        "assign_to": "Engineer",
        "feedback": "Reviewer agent failed to make a decision after multiple attempts. Defaulting to Engineer."
    })
