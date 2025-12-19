# Agent: Architect

## Role in the Team
The **Architect** is the "Brain" of the SOLO mode. It is responsible for creating the project structure, selecting necessary modules from the knowledge base, and writing the "pure" business logic code.

## Core Logic
1.  **Task Analysis:** Receives the user prompt.
2.  **Tool Retrieval (RAG):** Loads the module database (`modules_db.json`) and searches for suitable "building blocks".
3.  **Specification Generation:**
    *   Creates a JSON object with two fields:
        *   `pure_code`: Python code solving the task (Happy Path).
        *   `decorators`: List of decorators for reliability (`@safe_call`, `@retry`).
4.  **Strict Constraints:**
    *   **Relative Paths:** Absolute paths (`/app/...`) are forbidden. All paths must be relative (e.g., `project/main.py`).
    *   **Imports:** Must use exact import paths from the knowledge base.

## Interaction
*   **Input:** `ArchitectInput` (task_prompt).
*   **Output:** `ArchitectOutput` (pure_code, decorators).
*   **Next Step:** Passes the specification to the **Stitcher** component.
