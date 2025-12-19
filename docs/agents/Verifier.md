# Agent: Verifier (SecondaryVerifier)

## Role in the Team
The **Verifier** (QA Engineer) ensures that the generated MVP not only starts but actually performs the requested task.

## Core Logic (Verification-Driven Development)

The Verifier operates in two stages:

### 1. Runtime Analysis (Smoke Test)
*   Starts the MVP using `poetry run python run.py`.
*   Checks if the process starts without immediate errors (Exit Code 0).
*   Captures `stderr`/`stdout`.

### 2. Functional QA
If the server starts successfully:
1.  **Generate Test:** Asks LLM to write a specific Python script (`qa_verify.py`) to verify the app based on the User Task.
2.  **Isolation:** Installs tools (e.g., `httpx`) in the MVP environment.
3.  **Run Test:** Executes the generated script against the running server (`http://localhost:8000`).
4.  **Analyze:**
    *   **Success:** Script passes.
    *   **Failure:** Script fails (AssertionError, 404, etc.). Returns error log to Architect for Self-Healing.

## Interaction
*   **Input:** Path to compiled project, User Task.
*   **Output:** Status (Success/Error) and Feedback.
