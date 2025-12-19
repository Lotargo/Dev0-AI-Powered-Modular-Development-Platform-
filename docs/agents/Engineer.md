# Agent: Engineer

## Role in the Team
The **Engineer** is the "Programmer" of the team. Its task is to take the technical plan created by the Planner and turn it into working code. It generates both the module code and its tests, and performs initial verification.

## Core Logic
The Engineer's workflow is a strict pipeline:

1.  **Receive Plan:** Gets the JSON plan from the Orchestrator containing all specs.
2.  **Generate Prompt:**
    *   Inserts the plan into a detailed prompt with strict formatting instructions.
    *   Requires a single text block containing:
        1.  `_FILENAME: your_module_name.py_` marker.
        2.  Full module code.
        3.  `---TEST_CODE---` marker.
        4.  Full test code.
    *   **Quality Checklist:** Reminds LLM to import dependencies and use consistent naming.
    *   **Few-Shot Example:** Includes a high-quality test file example.
3.  **LLM Call:** Generates the code.
4.  **Parse & Clean:**
    *   Removes Markdown code blocks.
    *   Extracts filename, module code, and test code using regex.
5.  **Refine Tests:** Injects `sys.path` setup and standard imports (`json`, `requests`) into the test file to prevent `ImportError` and `NameError`.
6.  **Save Files:** Saves module to `project/modules/new/` and tests to `project/tests/new/`.
7.  **Run Tests:** Executes `poetry run pytest -v {tpath}` via `bash_runner`.
8.  **Return Result:**
    *   `TESTS_PASSED`: If exit code is 0. Returns paths and output.
    *   `TESTS_FAILED`: If exit code is non-zero. Returns output with errors.
    *   `ERROR`: On generation/parsing failure.

## Process Diagram

```mermaid
graph TD
    A[Start: execute] --> B[1. Generate Prompt with Plan];
    B --> C[2. LLM Generation];
    C --> D[3. Parse: Extract Filename, Code, Tests];
    D --> E[4. Refine Tests (Inject sys.path)];
    E --> F[5. Save .py files];
    F --> G[6. Run pytest];
    G --> H{Passed?};
    H --> |Yes| I[Return: status=TESTS_PASSED];
    H --> |No| J[Return: status=TESTS_FAILED];
    C --> |Error| K[Return: status=ERROR];
```
