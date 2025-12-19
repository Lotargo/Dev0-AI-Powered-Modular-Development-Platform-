# Agent: Orchestrator

## Role in the Team
The **Orchestrator** is the "Team Lead". It is the central entry point (`execute` method) that coordinates the work of all other agents. Its main responsibility is to make high-level decisions about the workflow and route the task between specialized agents.

## Core Logic

The Orchestrator's work consists of sequential steps (State Machine):

*   **Step 1: Analysis & Routing.**
    *   The Orchestrator receives the user task.
    *   It calls the **Router** (a specialized sub-agent) to determine the operating mode: `SOLO` (Classic) or `TEAM` (Research).
    *   **Decision:**
        *   If `SOLO`: The task is simple/standard.
        *   If `TEAM`: The task requires new functionality.

*   **Step 2: Planning (TEAM Mode only).**
    *   If `TEAM` mode is selected, the Orchestrator calls the **Planner**.
    *   **Statuses:**
        *   `TOOLS_SUFFICIENT`: The Planner found existing tools. Orchestrator skips development and jumps to Step 5 (Architect).
        *   `PLAN_CREATED`: A development plan is created. Orchestrator extracts the JSON plan and proceeds.
        *   `ERROR`: Abort.

*   **Step 3: Development.**
    *   The plan is serialized to JSON and passed to the **Engineer**.
    *   **Statuses:**
        *   `TESTS_PASSED`: Code generated and verified. Proceeds to Review.
        *   `TESTS_FAILED`: Engineer failed. Abort.

*   **Step 4: Review.**
    *   File paths are passed to the **Reviewer**.
    *   **Statuses:**
        *   `APPROVED`: Code approved. Orchestrator triggers indexing (`scripts/index_modules.py`) and proceeds.
        *   `REJECTED`: Reviewer rejected the code. Abort.

*   **Step 5: Final Assembly.**
    *   Orchestrator calls the **Architect** with the original user task. The Architect now has access to the newly created tools via the updated Knowledge Base.

## Process Diagram

```mermaid
graph TD
    A[Start: execute] --> B{mode == TEAM?};
    B --> |No (SOLO)| C[Call Architect];
    B --> |Yes (TEAM)| D[Call Planner];

    D --> E{Planner Status?};
    E --> |TOOLS_SUFFICIENT| C;
    E --> |PLAN_CREATED| F[Call Engineer];
    E --> |ERROR| Z[End: Error];

    F --> G{Engineer Status?};
    G --> |TESTS_PASSED| H[Call Reviewer];
    G --> |ERROR / FAILED| Z;

    H --> I{Reviewer Status?};
    I --> |APPROVED| J[Index New Module];
    I --> |REJECTED| Z;

    J --> C;
    C --> K[End: Success];
```
